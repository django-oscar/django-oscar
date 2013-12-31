from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


def get_user_model():
    """
    Return the User model

    Using this function instead of Django 1.5's get_user_model allows backwards
    compatibility with Django 1.4.
    """
    try:
        # Django 1.5+
        from django.contrib.auth import get_user_model
    except ImportError:
        # Django <= 1.4
        model = User
    else:
        model = get_user_model()

    # Test if user model has any custom fields and add attributes to the _meta
    # class
    core_fields = set([f.name for f in User._meta.fields])
    model_fields = set([f.name for f in model._meta.fields])
    new_fields = model_fields.difference(core_fields)
    model._meta.has_additional_fields = len(new_fields) > 0
    model._meta.additional_fields = new_fields

    return model


# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
# Two additional settings that are useful in South migrations when
# specifying the user model in the FakeORM
try:
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit('.', 1)
except ValueError:
    raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form"
                               " 'app_label.model_name'")


def format_html(format_string, *args, **kwargs):
    """
    Backport of format_html from Django 1.5+ to support Django 1.4
    """
    args_safe = map(conditional_escape, args)
    kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in
                        six.iteritems(kwargs)])
    return mark_safe(format_string.format(*args_safe, **kwargs_safe))
