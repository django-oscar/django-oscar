from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class Emailbackend(ModelBackend):
    def authenticate(self, email=None, password=None, *args, **kwargs):
        if not email:
            email = kwargs.pop('username', None)
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
