from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from oscar.apps.catalogue.middleware import CurrencyMiddleware


class TestCurrencyMiddleware(TestCase):

    @staticmethod
    def get_response_for_test(request):
        return HttpResponse()

    @override_settings(OSCAR_DEFAULT_CURRENCY='CUR')
    def test_currency_set_on_request(self):
        request = RequestFactory().get('/')
        CurrencyMiddleware(self.get_response_for_test)(request)

        self.assertEqual(request.currency, 'CUR')
