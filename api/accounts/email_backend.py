from django.utils import timezone
from django.contrib.auth import get_user_model


def authenticate(username=None, password=None,):
    msg = "Invalid Credentials."
    UserModel = get_user_model()

    try:
        user = UserModel.objects.get(email=username)
    except UserModel.DoesNotExist:
        return None, msg
    if not user.is_active:
        return None, "Account not yet activated."
    if user is not None:
        if user.failed_login_attempts >= 5 and user.last_failed_login_attempt is not None:
            # Check if the last failed login attempt was more than 24 hours ago
            elapsed_time = timezone.now() - user.last_failed_login_attempt
            if elapsed_time.total_seconds() >= 24 * 60 * 60:
                # Reset failed login attempts and allow login
                user.failed_login_attempts = 0
            else:
                # Disable the account for 24 hours
                user.login_limit = True
                msg = "Account has been disabled for 24 hours."
        else:
            # Reset failed login attempts if the login was successful
            if user.check_password(password):
                user.failed_login_attempts = 0
                # Enable account
                user.login_limit = False
                user.save()
                return user, f"Hi, {user.first_name}. Welcome"
            else:
                # Increment failed login attempts and record the time
                user.failed_login_attempts += 1
                user.last_failed_login_attempt = timezone.now()

        user.save()

    return None, msg

