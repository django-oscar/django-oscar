from unidecode import unidecode
from django.conf import settings


def slugify(value):
    """
    Slugify a string (even if it contains non-ASCII chars)
    """
    # Re-map some strings to avoid important characters being stripped.  Eg
    # remap 'c++' to 'cpp' otherwise it will become 'c'.
    if hasattr(settings, 'OSCAR_SLUG_MAP'):
        for k, v in settings.OSCAR_SLUG_MAP.items():
            value = value.replace(k, v)

    # Allow an alternative slugify function to be specified
    if hasattr(settings, 'OSCAR_SLUG_FUNCTION'):
        slugifier = settings.OSCAR_SLUG_FUNCTION
    else:
        from django.template import defaultfilters
        slugifier = defaultfilters.slugify

    # Use unidecode to convert non-ASCII strings to ASCII equivalents where
    # possible.
    value = slugifier(
        unidecode(unicode(value)))

    # Remove stopwords
    if hasattr(settings, 'OSCAR_SLUG_BLACKLIST'):
        for word in settings.OSCAR_SLUG_BLACKLIST:
            value = value.replace(word + '-', '')
            value = value.replace('-' + word, '')

    return value
