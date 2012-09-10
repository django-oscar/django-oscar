from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class Emailbackend(ModelBackend):
    def authenticate(self, email=None, password=None, *args, **kwargs):
        if not email:
            if not 'username' in kwargs:
                return None
            email = kwargs['username']
        email = email.lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
