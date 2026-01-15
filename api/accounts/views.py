"""
Authentication views for OTP-based authentication with JWT issuance.
"""

import os
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging
import random
import string
import redis

from .serializers import OTPRequestSerializer, OTPVerifySerializer, UserSerializer
from .tasks import send_otp_email, write_audit_log

User = get_user_model()
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)


# ============================================================================
# HELPER FUNCTIONS AND CLASSES (Moved from helper folder)
# ============================================================================

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


class OTPService:
    """Handles OTP generation, storage, and verification"""
    
    OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))
    OTP_EXPIRY_SECONDS = int(os.getenv('OTP_EXPIRY_SECONDS', 300))  # 5 minutes
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=self.OTP_LENGTH))
    
    def store_otp(self, email, otp):
        """Store OTP in Redis with 5-minute TTL"""
        key = f"otp:{email}"
        redis_client.setex(key, self.OTP_EXPIRY_SECONDS, otp)
        return True
    
    def verify_otp(self, email, otp):
        """
        Verify OTP and delete it (one-time use)
        Returns: True if valid, False otherwise
        """
        key = f"otp:{email}"
        stored_otp = redis_client.get(key)
        
        if not stored_otp:
            return False
        
        if stored_otp != otp:
            return False
        
        # Delete OTP after successful verification (one-time use)
        redis_client.delete(key)
        return True


class RateLimiter:
    """Handles rate limiting for OTP requests and failed attempts"""
    
    # Email rate limiting: 3 requests per 10 minutes
    EMAIL_LIMIT = int(os.getenv('EMAIL_LIMIT', 3))
    EMAIL_WINDOW_SECONDS = int(os.getenv('EMAIL_WINDOW_SECONDS', 600))  # 10 minutes
    
    # IP rate limiting: 10 requests per 1 hour
    IP_LIMIT = int(os.getenv('IP_LIMIT', 10))
    IP_WINDOW_SECONDS = int(os.getenv('IP_WINDOW_SECONDS', 3600))  # 1 hour
    
    # Failed attempts: 5 attempts per 15 minutes
    FAILED_LIMIT = int(os.getenv('FAILED_LIMIT', 5))
    FAILED_WINDOW_SECONDS = int(os.getenv('FAILED_WINDOW_SECONDS', 900))  # 15 minutes
    
    def is_email_rate_limited(self, email):
        """
        Check email rate limit (3 per 10 minutes)
        Returns: (is_limited: bool, retry_after_seconds: int)
        """
        key = f"ratelimit:email:{email}"
        current = redis_client.incr(key)
        
        if current == 1:
            # First request, set TTL
            redis_client.expire(key, self.EMAIL_WINDOW_SECONDS)
        
        if current > self.EMAIL_LIMIT:
            ttl = redis_client.ttl(key)
            return True, ttl
        
        return False, 0
    
    def is_ip_rate_limited(self, ip_address):
        """
        Check IP rate limit (10 per 1 hour)
        Returns: (is_limited: bool, retry_after_seconds: int)
        """
        key = f"ratelimit:ip:{ip_address}"
        current = redis_client.incr(key)
        
        if current == 1:
            redis_client.expire(key, self.IP_WINDOW_SECONDS)
        
        if current > self.IP_LIMIT:
            ttl = redis_client.ttl(key)
            return True, ttl
        
        return False, 0
    
    def track_failed_attempt(self, email):
        """
        Track failed OTP verification attempt
        Returns: (is_locked: bool, unlock_eta_seconds: int)
        """
        key = f"failed_otp:{email}"
        current = redis_client.incr(key)
        
        if current == 1:
            redis_client.expire(key, self.FAILED_WINDOW_SECONDS)
        
        if current >= self.FAILED_LIMIT:
            ttl = redis_client.ttl(key)
            return True, ttl
        
        return False, 0
    
    def is_email_locked(self, email):
        """
        Check if account is locked due to failed attempts
        Returns: (is_locked: bool, unlock_eta_seconds: int)
        """
        key = f"failed_otp:{email}"
        count = redis_client.get(key)
        
        if count and int(count) >= self.FAILED_LIMIT:
            ttl = redis_client.ttl(key)
            return True, ttl
        
        return False, 0
    
    def clear_failed_attempts(self, email):
        """Clear failed attempts after successful verification"""
        key = f"failed_otp:{email}"
        redis_client.delete(key)
        return True


# ============================================================================
# OTP REQUEST ENDPOINT
# ============================================================================

class OTPRequestView(APIView):
    """
    OTP Request endpoint.
    
    POST /api/v1/auth/otp/request
    
    Issues a 6-digit OTP via email with rate limiting:
    - Max 3 requests per email per 10 minutes
    - Max 10 requests per IP per 1 hour
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=OTPRequestSerializer,
        responses={
            202: OpenApiResponse(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "OTP sent to your email",
                        "status_code": 202,
                        "data": {
                            "email": "user@example.com",
                            "expiry_seconds": 300
                        }
                    }
                }
            ),
            429: OpenApiResponse(
                description="Rate limit exceeded",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Too many OTP requests. Please try again later.",
                        "status_code": 429,
                        "data": {
                            "retry_after_seconds": 120
                        }
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid request"),
        },
        summary="Request an OTP",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid request",
                    "status_code": 400,
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)
        user_agent = get_client_user_agent(request)
        
        # Initialize rate limiters
        rate_limiter = RateLimiter()
        
        # Check email rate limit (max 3 per 10 minutes)
        email_limited, email_retry = rate_limiter.is_email_rate_limited(email)
        if email_limited:
            # Enqueue audit log for rate limit hit
            write_audit_log.delay(
                'OTP_REQUESTED',
                email,
                ip_address,
                user_agent,
                {'reason': 'Email rate limit exceeded'}
            )
            return Response(
                {
                    "success": False,
                    "message": "Too many OTP requests. Please try again later.",
                    "status_code": 429,
                    "data": {
                        "retry_after_seconds": email_retry
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Check IP rate limit (max 10 per 1 hour)
        ip_limited, ip_retry = rate_limiter.is_ip_rate_limited(ip_address)
        if ip_limited:
            write_audit_log.delay(
                'OTP_REQUESTED',
                email,
                ip_address,
                user_agent,
                {'reason': 'IP rate limit exceeded'}
            )
            return Response(
                {
                    "success": False,
                    "message": "Too many OTP requests from this IP. Please try again later.",
                    "status_code": 429,
                    "data": {
                        "retry_after_seconds": ip_retry
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Generate and store OTP
        otp_service = OTPService()
        otp = otp_service.generate_otp()
        otp_service.store_otp(email, otp)
        
        # Enqueue async tasks
        send_otp_email.delay(email, otp)
        write_audit_log.delay(
            'OTP_REQUESTED',
            email,
            ip_address,
            user_agent,
            {}
        )
        
        logger.info(f"OTP requested for {email} from {ip_address}")
        
        return Response(
            {
                "success": True,
                "message": "OTP sent to your email",
                "status_code": 202,
                "data": {
                    "email": email,
                    "expiry_seconds": otp_service.OTP_EXPIRY_SECONDS
                }
            },
            status=status.HTTP_202_ACCEPTED
        )


# ============================================================================
# OTP VERIFY ENDPOINT
# ============================================================================

class OTPVerifyView(APIView):
    """
    OTP Verification endpoint.
    
    POST /api/v1/auth/otp/verify
    
    Verifies OTP and issues JWT tokens on success.
    Implements lockout after 5 failed attempts in 15 minutes.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=OTPVerifySerializer,
        responses={
            201: OpenApiResponse(
                description="OTP verified, user created/updated, tokens issued",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "OTP verified successfully",
                        "status_code": 201,
                        "data": {
                            "user": {
                                "id": 1,
                                "email": "user@example.com",
                                "first_name": "",
                                "last_name": "",
                                "is_active": True,
                                "date_joined": "2025-01-13T10:00:00Z"
                            },
                            "access": "<JWT_ACCESS_TOKEN>",
                            "refresh": "<JWT_REFRESH_TOKEN>"
                        }
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid OTP"),
            423: OpenApiResponse(
                description="Account locked due to too many failed attempts",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Account locked due to too many failed attempts",
                        "status_code": 423,
                        "data": {
                            "unlock_eta_seconds": 600
                        }
                    }
                }
            ),
            429: OpenApiResponse(description="Too many failed attempts")
        },
        summary="Verify OTP and get JWT tokens",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid request",
                    "status_code": 400,
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        ip_address = get_client_ip(request)
        user_agent = get_client_user_agent(request)
        
        rate_limiter = RateLimiter()
        otp_service = OTPService()
        
        # Check if email is locked
        is_locked, unlock_eta = rate_limiter.is_email_locked(email)
        if is_locked:
            write_audit_log.delay(
                'OTP_LOCKED',
                email,
                ip_address,
                user_agent,
                {'attempt_number': 'locked'}
            )
            return Response(
                {
                    "success": False,
                    "message": "Account locked due to too many failed attempts",
                    "status_code": 423,
                    "data": {
                        "unlock_eta_seconds": unlock_eta
                    }
                },
                status=status.HTTP_423_LOCKED
            )
        
        # Verify OTP
        if not otp_service.verify_otp(email, otp):
            # Track failed attempt
            is_now_locked, lockout_eta = rate_limiter.track_failed_attempt(email)
            
            if is_now_locked:
                write_audit_log.delay(
                    'OTP_LOCKED',
                    email,
                    ip_address,
                    user_agent,
                    {'reason': 'Max failed attempts exceeded'}
                )
                return Response(
                    {
                        "success": False,
                        "message": "Account locked due to too many failed attempts",
                        "status_code": 423,
                        "data": {
                            "unlock_eta_seconds": lockout_eta
                        }
                    },
                    status=status.HTTP_423_LOCKED
                )
            
            # Still have attempts left
            write_audit_log.delay(
                'OTP_FAILED',
                email,
                ip_address,
                user_agent,
                {}
            )
            
            return Response(
                {
                    "success": False,
                    "message": "Invalid OTP",
                    "status_code": 400,
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP verified successfully
        # Create or update user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email}
        )
        
        # Clear failed attempts
        rate_limiter.clear_failed_attempts(email)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Enqueue audit log
        write_audit_log.delay(
            'OTP_VERIFIED',
            email,
            ip_address,
            user_agent,
            {'user_id': user.id, 'user_created': created}
        )
        
        logger.info(f"OTP verified for {email} from {ip_address}")
        
        return Response(
            {
                "success": True,
                "message": "OTP verified successfully",
                "status_code": 201,
                "data": {
                    "user": UserSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            },
            status=status.HTTP_201_CREATED
        )