import re

from django.conf import settings
from django.core.cache import cache

from oscar.core.loading import get_model


Configuration = get_model('system', 'Configuration')


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


def get_system_configuration(request):
    """ 
    Get and cache the system configuration. This is updated every hour.
    Instead of using settings, lookup system configuration from the database.
    """
    config = cache.get('system-config')
    if not config:
        # Lookup or create the configuration
        system_config = Configuration.objects.first()
        if system_config is None:
            system_config = Configuration(
                shop_name=settings.OSCAR_SHOP_NAME,
                shop_tagline=settings.OSCAR_SHOP_TAGLINE,
                homepage_url=settings.OSCAR_HOMEPAGE,
                # Fallback to old settings name for backwards compatibility
                use_less=(
                    getattr(settings, 'OSCAR_USE_LESS', None) or
                    getattr(settings, 'USE_LESS', False)
                ),
                google_analytics_id=(
                    getattr(settings, 'OSCAR_GOOGLE_ANALYTICS_ID', None) or
                    getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
                )    
            )
            system_config.save()
        config = system_config.as_context()
        cache.set('system-config', config, 360)
    return config


def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    config = get_system_configuration(request)
    config['language_neutral_url_path'] = strip_language_code(request)
    return config
