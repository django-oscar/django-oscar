from decimal import Decimal as D
import httplib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, clear_url_caches
from django.conf import settings

from oscar.test.helpers import create_product
from oscar.test import ClientTestCase


class AnonymousCheckoutViewsTests(ClientTestCase):
    is_anonymous = True

    def test_index_does_not_require_login(self):
        url = reverse('checkout:index')
        response = self.client.get(url)
        self.assertIsOk(response)

    def test_user_address_views_require_a_login(self):
        urls = [reverse('checkout:user-address-create'),
                reverse('checkout:user-address-update', kwargs={'pk': 1}),
                reverse('checkout:user-address-delete', kwargs={'pk': 1}),]
        for url in urls:
            response = self.client.get(url)
            self.assertIsRedirect(response)

    def test_core_checkout_requires_login(self):
        urls = [reverse('checkout:shipping-address'),
                reverse('checkout:payment-method'),
                reverse('checkout:shipping-method'),
                reverse('checkout:payment-details')]
        for url in urls:
            response = self.client.get(url)
            self.assertIsRedirect(response)


class ShippingAddressViewTests(ClientTestCase):
    fixtures = ['countries.json']
    
    def test_anon_checkout_disabled_by_default(self):
        self.assertFalse(settings.OSCAR_ALLOW_ANON_CHECKOUT)

    def test_create_shipping_address_adds_address_to_session(self):
        response = self.client.post(reverse('checkout:shipping-address'),
                                            {'last_name': 'Doe',
                                             'line1': '1 Egg Street',
                                             'postcode': 'N1 9RT',
                                             'country': 'GB',
                                            })
        self.assertIsRedirect(response)
        session_address = self.client.session['checkout_data']['shipping']['new_address_fields']
        self.assertEqual('Doe', session_address['last_name'])
        self.assertEqual('1 Egg Street', session_address['line1'])
        self.assertEqual('N1 9RT', session_address['postcode'])


class CheckoutMixin(object):
    fixtures = ['countries.json']

    def complete_shipping_address(self):
        response = self.client.post(reverse('checkout:shipping-address'),
                                     {'last_name': 'Doe',
                                      'line1': '1 Egg Street',
                                      'postcode': 'N1 9RT',
                                      'country': 'GB',
                                     })
        self.assertIsRedirect(response)


class ShippingMethodViewTests(ClientTestCase, CheckoutMixin):
    fixtures = ['countries.json']

    def test_shipping_method_view_redirects_if_no_shipping_address(self):
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse('checkout:shipping-address'))

    def test_redirects_by_default(self):
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:shipping-method'))
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse('checkout:payment-method'))


class PaymentMethodViewTests(ClientTestCase, CheckoutMixin):

    def test_view_redirects_if_no_shipping_address(self):
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse('checkout:shipping-address'))

    def test_view_redirects_if_no_shipping_method(self):
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse('checkout:shipping-method'))
