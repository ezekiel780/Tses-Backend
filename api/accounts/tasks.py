"""
Celery tasks for asynchronous operations.
"""

import logging

from celery import shared_task

from audit.models import AuditLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_otp_email(self, email: str, otp: str):
    """
    Asynchronous task to send OTP email.
    In production, this would integrate with an email service (e.g., SendGrid, AWS SES).
    For now, we log to console.
    """
    try:
        # In a real application, you would send an email here
        logger.info(f"[OTP EMAIL] Sending OTP to {email}: {otp}")
        print(f"\n{'='*60}")
        print(f"[OTP EMAIL TASK]")
        print(f"Recipient: {email}")
        print(f"OTP: {otp}")
        print(f"{'='*60}\n")
        return f"Email sent to {email}"
    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def write_audit_log(self, event: str, email: str, ip_address: str, 
                    user_agent: str = "", metadata: dict = None):
    """
    Asynchronous task to write audit log entries.
    Creates an AuditLog record for tracking authentication events.
    """
    try:
        if metadata is None:
            metadata = {}
        
        audit_log = AuditLog.objects.create(
            event=event,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        logger.info(f"Audit log created: {event} for {email} from {ip_address}")
        return f"Audit log {audit_log.id} created for {event}"
    except Exception as exc:
        logger.error(f"Failed to write audit log: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)
