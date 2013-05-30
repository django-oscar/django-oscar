from django.conf import settings


def get_user_model():
    """
    Using this function instead of Django 1.5's get_user_model allows backwards
    compatibility with Django 1.4.
    """
    try:
        # Django 1.5+
        from django.contrib.auth import get_user_model
    except ImportError:
        # Django <= 1.4
        from django.contrib.auth.models import User
        return User
    else:
        return get_user_model()


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
