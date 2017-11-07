import django
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured

from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model

User = get_user_model()

if hasattr(User, 'REQUIRED_FIELDS'):
    if not (User.USERNAME_FIELD == 'email' or 'email' in User.REQUIRED_FIELDS):
        raise ImproperlyConfigured(
            "EmailBackend: Your User model must have an email"
            " field with blank=False")


class EmailBackend(ModelBackend):
    """
    Custom auth backend that uses an email address and password

    For this to work, the User model must have an 'email' field
    """

    def _authenticate(self, request, email=None, password=None, *args, **kwargs):
        if email is None:
            if 'username' not in kwargs or kwargs['username'] is None:
                return None
            clean_email = normalise_email(kwargs['username'])
        else:
            clean_email = normalise_email(email)

        # Check if we're dealing with an email address
        if '@' not in clean_email:
            return None

        # Since Django doesn't enforce emails to be unique, we look for all
        # matching users and try to authenticate them all. Note that we
        # intentionally allow multiple users with the same email address
        # (has been a requirement in larger system deployments),
        # we just enforce that they don't share the same password.
        # We make a case-insensitive match when looking for emails.
        matching_users = User.objects.filter(email__iexact=clean_email)
        authenticated_users = [
            user for user in matching_users if (user.check_password(password) and self.user_can_authenticate(user))]
        if len(authenticated_users) == 1:
            # Happy path
            return authenticated_users[0]
        elif len(authenticated_users) > 1:
            # This is the problem scenario where we have multiple users with
            # the same email address AND password. We can't safely authenticate
            # either.
            raise User.MultipleObjectsReturned(
                "There are multiple users with the given email address and "
                "password")
        return None

    # The signature of the authenticate method changed in Django 1.11 to include
    # a mandatory `request` argument.
    if django.VERSION < (1, 11):
        def authenticate(self, email=None, password=None, *args, **kwargs):
            return self._authenticate(None, email, password, *args, **kwargs)
    else:
        def authenticate(self, *args, **kwargs):
            return self._authenticate(*args, **kwargs)

    if django.VERSION < (1, 10):
        def user_can_authenticate(self, user):
            # user_can_authenticate was introduced in Django 1.10. Prior to that
            # inactive users could log in. That behaviour is retained for Django < 1.10.
            return True
