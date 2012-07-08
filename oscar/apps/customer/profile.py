from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.utils.translation import ugettext as _


def get_profile_class():
    """
    Return the profile model class
    """
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    profile_class = get_model(app_label, model_name)
    if not profile_class:
        raise ImproperlyConfigured(_("Can't import profile model"))
    return profile_class
