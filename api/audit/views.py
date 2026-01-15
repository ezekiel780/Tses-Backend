from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from datetime import datetime
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogPagination(PageNumberPagination):
    """Custom pagination for audit logs"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reading audit logs.
    
    Supports filtering by:
    - email: Filter by email address
    - event: Filter by event type (OTP_REQUESTED, OTP_VERIFIED, OTP_FAILED, OTP_LOCKED)
    - from: Filter by start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    - to: Filter by end date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['email', 'event']
    ordering = ['-created_at']
    ordering_fields = ['created_at']
    pagination_class = AuditLogPagination
    
    def get_queryset(self):
        """Apply date range filtering"""
        queryset = super().get_queryset()
        
        # Filter by from date
        from_date = self.request.query_params.get('from')
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
                queryset = queryset.filter(created_at__gte=from_dt)
            except ValueError:
                pass
        
        # Filter by to date
        to_date = self.request.query_params.get('to')
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date)
                queryset = queryset.filter(created_at__lte=to_dt)
            except ValueError:
                pass
        
        return queryset
    
    @extend_schema(
        description="List all audit logs with optional filtering and pagination",
        parameters=[
            {
                'name': 'email',
                'in': 'query',
                'description': 'Filter by email address',
                'schema': {'type': 'string', 'format': 'email'}
            },
            {
                'name': 'event',
                'in': 'query',
                'description': 'Filter by event type',
                'schema': {'type': 'string', 'enum': ['OTP_REQUESTED', 'OTP_VERIFIED', 'OTP_FAILED', 'OTP_LOCKED']}
            },
            {
                'name': 'from',
                'in': 'query',
                'description': 'Filter from date (ISO format)',
                'schema': {'type': 'string', 'format': 'date-time'}
            },
            {
                'name': 'to',
                'in': 'query',
                'description': 'Filter to date (ISO format)',
                'schema': {'type': 'string', 'format': 'date-time'}
            },
        ],
        tags=["Audit Logs"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    