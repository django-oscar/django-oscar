from unidecode import unidecode
from django.template import defaultfilters


def slugify(value):
    """
    Slugify a string (even if it contains non-ASCII chars)
    """
    return defaultfilters.slugify(
        unidecode(unicode(value)))
