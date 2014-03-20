from __future__ import absolute_import  # for logging import below
import logging
import six

from django.utils.timezone import get_current_timezone, is_naive, make_aware
from django.conf import settings
from django.template.defaultfilters import (date as date_filter,
                                            slugify as django_slugify)
from unidecode import unidecode

from oscar.core.loading import import_string


def default_slugifier(value):
    """
    Oscar's default slugifier function.
    Uses Django's slugify function, but first applies unidecode() to convert
    non-ASCII strings to ASCII equivalents where possible.
    """
    return django_slugify(value)


def slugify(value):
    """
    Slugify a string (even if it contains non-ASCII chars)
    """
    # Re-map some strings to avoid important characters being stripped.  Eg
    # remap 'c++' to 'cpp' otherwise it will become 'c'.
    for k, v in settings.OSCAR_SLUG_MAP.items():
        value = value.replace(k, v)

    # Allow an alternative slugify function to be specified
    # Recommended way to specify a function is as a string
    slugifier = getattr(settings, 'OSCAR_SLUG_FUNCTION', default_slugifier)
    if isinstance(slugifier, six.string_types):
        slugifier = import_string(slugifier)

    # Use unidecode to convert non-ASCII strings to ASCII equivalents where
    # possible.
    value = slugifier(unidecode(six.text_type(value)))

    # Remove stopwords
    for word in settings.OSCAR_SLUG_BLACKLIST:
        value = value.replace(word + '-', '')
        value = value.replace('-' + word, '')

    return value


def compose(*functions):
    """
    Compose functions

    This is useful for combining decorators.
    """
    def _composed(*args):
        for fn in functions:
            try:
                args = fn(*args)
            except TypeError:
                # args must be scalar so we don't try to expand it
                args = fn(args)
        return args
    return _composed


def format_datetime(dt, format=None):
    """
    Takes an instance of datetime, converts it to the current timezone and
    formats it as a string. Use this instead of
    django.core.templatefilters.date, which expects localtime.

    :param format: Common will be settings.DATETIME_FORMAT or
                   settings.DATE_FORMAT, or the resp. shorthands
                   ('DATETIME_FORMAT', 'DATE_FORMAT')
    """
    if is_naive(dt):
        localtime = make_aware(dt, get_current_timezone())
        logging.warning(
            "oscar.core.utils.format_datetime received native datetime")
    else:
        localtime = dt.astimezone(get_current_timezone())
    return date_filter(localtime, format)
