from decimal import Decimal as D
import httplib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, clear_url_caches
from django.conf import settings

from oscar.test.helpers import create_product


class AnonCheckoutTests(TestCase):

    def setUp(self):
        clear_url_caches()
        self.client = Client()
        settings.OSCAR_ALLOW_ANON_CHECKOUT = True

    def tearDown(self):
        settings.OSCAR_ALLOW_ANON_CHECKOUT = False

    def _test_shipping_address_does_require_login(self):
        # Disabled until I can work out how to reload the URL config between tests
        url = reverse('checkout:shipping-address')
        response = self.client.get(url)
        self.assertEquals(httplib.OK, response.status_code)
    

class CheckoutViewsTest(TestCase):
    fixtures = ['example-shipping-charges.json']
    
    def setUp(self):
        clear_url_caches()
        self.client = Client()
        super(CheckoutViewsTest, self).setUp()
    
    def test_user_address_views_require_a_login(self):
        urls = [reverse('checkout:user-address-create'),
                reverse('checkout:user-address-update', kwargs={'pk': 1}),
                reverse('checkout:user-address-delete', kwargs={'pk': 1}),]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(httplib.FOUND, response.status_code)

    def test_anon_checkout_disabled_by_default(self):
        self.assertFalse(settings.OSCAR_ALLOW_ANON_CHECKOUT)

    def test_index_does_not_require_login(self):
        url = reverse('checkout:index')
        response = self.client.get(url)
        self.assertEquals(httplib.OK, response.status_code)

    def test_core_checkout_requires_login(self):
        urls = [reverse('checkout:shipping-address'),
                reverse('checkout:payment-method'),
                reverse('checkout:shipping-method'),
                reverse('checkout:payment-details')]
        for url in urls:
            response = self.client.get(url)
            self.assertEquals(httplib.FOUND, response.status_code)
