from django.conf import settings


def metadata(request):
    return {'version': getattr(settings, 'VERSION', 'N/A')}