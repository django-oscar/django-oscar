from django.conf import settings


def metadata(request):
    return {'version': getattr(settings, 'VERSION', 'N/A'),
            'shop_name': settings.OSCAR_SHOP_NAME,
            'google_analytics_id': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}