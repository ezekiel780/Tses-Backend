from django.db import models


class AuditLog(models.Model):
    """Audit log model to track all authentication events"""
    
    EVENT_CHOICES = (
        ('OTP_REQUESTED', 'OTP Requested'),
        ('OTP_VERIFIED', 'OTP Verified'),
        ('OTP_FAILED', 'OTP Failed'),
        ('OTP_LOCKED', 'OTP Locked'),
    )
    
    id = models.BigAutoField(primary_key=True)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES, db_index=True)
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['event', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event} - {self.email} - {self.created_at}"
    