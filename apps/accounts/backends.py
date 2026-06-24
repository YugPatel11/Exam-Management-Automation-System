from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    Superusers can still log in using their username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        # Try to find the user by email first
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            # If not found by email, try by username
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
                
        # If user is found, check the password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
