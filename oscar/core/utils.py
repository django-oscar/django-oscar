from unidecode import unidecode
from django.template import defaultfilters
from django.conf import settings


def slugify(value):
    """
    Slugify a string (even if it contains non-ASCII chars)
    """
    if hasattr(settings, 'OSCAR_SLUG_MAP'):
        for k, v in settings.OSCAR_SLUG_MAP.items():
            value = value.replace(k, v)
    return defaultfilters.slugify(
        unidecode(unicode(value)))
