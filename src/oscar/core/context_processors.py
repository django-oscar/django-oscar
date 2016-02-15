import platform
import re

import django
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.six.moves.urllib import parse

import oscar


def strip_language_code(request):
    """
    When using Django's i18n_patterns, we need a language-neutral variant of
    the current URL to be able to use set_language to change languages.
    This naive approach strips the language code from the beginning of the URL
    and will likely fail if using translated URLs.
    """
    path = request.path
    if settings.USE_I18N and hasattr(request, 'LANGUAGE_CODE'):
        return re.sub('^/%s/' % request.LANGUAGE_CODE, '/', path)
    return path


def usage_statistics_string():
    """
    For Oscar development, it is helpful to know which versions of Oscar,
    Django and Python are in use, and which can be safely deprecated or
    removed. If tracking is enabled, this function builds a query string with
    that information. It is used in dashboard/layout.html with an invisible
    tracker pixel.
    If you're developing locally or tracking is disabled, the tracker pixel
    does not get rendered and no information is collected.
    """
    if not settings.DEBUG and getattr(settings, 'OSCAR_TRACKING', True):
        params = {
            'django': django.get_version(),
            'python': platform.python_version(),
            'oscar': oscar.get_version(),
        }
        return mark_safe(parse.urlencode(params))
    else:
        return None


def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    return {'display_version': getattr(settings, 'DISPLAY_VERSION', False),
            'version': getattr(settings, 'VERSION', 'N/A'),
            'shop_name': settings.OSCAR_SHOP_NAME,
            'shop_tagline': settings.OSCAR_SHOP_TAGLINE,
            'homepage_url': settings.OSCAR_HOMEPAGE,
            'use_less': getattr(settings, 'USE_LESS', False),
            'call_home': usage_statistics_string(),
            'language_neutral_url_path': strip_language_code(request),
            'google_analytics_id': getattr(settings,
                                           'GOOGLE_ANALYTICS_ID', None)}
