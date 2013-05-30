from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from oscar.core.compat import get_user_model

User = get_user_model()

if User._meta.get_field('email').blank:
    raise ImproperlyConfigured("Emailbackend: Your User model must have an email"
                               " field with blank=False")


class Emailbackend(ModelBackend):

    def authenticate(self, email=None, password=None, *args, **kwargs):
        if email is None:
            if not 'username' in kwargs or kwargs['username'] is None:
                return None
            email = kwargs['username']

        # Check if we're dealing with an email address
        if '@' not in email:
            return None

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
