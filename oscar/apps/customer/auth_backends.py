from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class Emailbackend(ModelBackend):

    def authenticate(self, email=None, password=None, *args, **kwargs):
        if email is None:
            if not 'username' in kwargs or kwargs['username'] is None:
                return None
            email = kwargs['username']

        # We lowercase the host part as this is what Django does when saving a
        # user
        local, host = email.split('@')
        clean_email = local + '@' + host.lower()
        try:
            user = User.objects.get(email=clean_email)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
