from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.contrib.auth.models import update_last_login
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import pytz

from .models import CustomUser, ActivationCode
from .services import CustomResponse, PasswordConfig


class ResetPasswordValidateToken(APIView):
    def post(self, request):
        email = request.data.get("email")
        reset_code = request.data.get("reset_code")

        if not email or not reset_code:
            return CustomResponse(False, "All fields are required!", 400)
        
        user_object = CustomUser.objects.filter(email=email)

        if not user_object.exists():
            return CustomResponse(False, "User not found", 404)
        
        user = user_object.get()
        activation_code_object = user.activation_code

        start = datetime.now(pytz.utc)
        end = datetime.fromisoformat(str(activation_code_object.expiry_date))
        if end.tzinfo is None:
            end = end.replace(tzinfo=pytz.utc)

        # Compute time difference
        time_difference = abs(end - start)

        if time_difference.total_seconds() > PasswordConfig.RESET_EXPIRY_SECONDS:
            return CustomResponse(False, "Invalid reset code: Code expired", 400)
        
        if not activation_code_object.verified : 
            return CustomResponse(False, "Reset code is invalid", 400)
        
        if not (reset_code == activation_code_object.code):
            return CustomResponse(False,"Invalid reset code", 400)
        
        user = get_object_or_404(CustomUser, email=email)
        update_last_login(None, user=user)
        # Token generation would use your existing token system
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        activation_code_object.verified = False
        activation_code_object.save()

        return CustomResponse(True, "Code verified successfully", 200, data=str(token.key))


class ResetPasswordConfirm(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email = request.user.email
        password = request.data.get("password")
        
        if not email or not password:
            return CustomResponse(False, "All fields are required", 400)
        
        if len(password) < 8:
            return CustomResponse(False, "Please enter a stronger password", 400)
        
        user_object = CustomUser.objects.filter(email=email)

        if not user_object.exists():
            return CustomResponse(False, "User not found", 404)
        
        user = user_object.get()
        user.set_password(password)
        user.save()

        return CustomResponse(True, "Password reset successfully", 200)


class ResetPasswordRequestToken(APIView):
    def post(self, request):
        email = request.data.get("email")

        if email is None:
            return CustomResponse(False, "Kindly provide the email address.", 400)
 
        user_object = CustomUser.objects.filter(email=email)
        if not user_object.exists():
            return CustomResponse(True, "Email address not found!", 404)
        
        user = user_object.get()
        activation_code_object = user.activation_code
        reset_code = ActivationCode.generate_activation_code()

        activation_code_object.count =  activation_code_object.count  + 1
        activation_code_object.code = reset_code
        activation_code_object.expiry_date = ActivationCode.default_expiry_date()
        activation_code_object.updated_at = timezone.now()
        if not activation_code_object.verified:
            activation_code_object.verified = True
        activation_code_object.save()

        mail_message = ActivationCode.generate_reset_code_message(code=reset_code)
        # send_a_mail("Password Reset", mail_message, email, True)  # Uncomment when email task is available
        return CustomResponse(True, "A token has been sent to your email.", 200)


