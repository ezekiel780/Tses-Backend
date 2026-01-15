import os
from rest_framework.response import Response

# -----------------------------
# Custom Response Class
# -----------------------------
class CustomResponse(Response):
    """
    Standardized response for all API views.
    """
    def __init__(self, success: bool, message: str, status_code: int = 200, data=None):
        payload = {
            "success": success,
            "message": message
        }
        if data is not None:
            payload["data"] = data
        super().__init__(data=payload, status=status_code)


# -----------------------------
# Password Reset / OTP Config
# -----------------------------
class PasswordConfig:
    """
    Configurable settings for password reset tokens and expiry.
    Reads from environment variables if available.
    """
    RESET_EXPIRY_SECONDS = int(os.getenv("PASSWORD_RESET_EXPIRY_SECONDS", 600))


    

