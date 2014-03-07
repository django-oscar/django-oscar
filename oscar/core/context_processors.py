from django.conf import settings


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
            # Whether to use a tracker gif in the dashboard to call back to one
            # of Tangent's servers.
            'call_home': getattr(settings, 'OSCAR_TRACKING', True),
            'google_analytics_id': getattr(settings,
                                           'GOOGLE_ANALYTICS_ID', None)}
