from django.conf import settings


class CurrencyMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "currency", settings.OSCAR_DEFAULT_CURRENCY)
        return self.get_response(request)
