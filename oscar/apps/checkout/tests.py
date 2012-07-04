from decimal import Decimal as D
import sys

from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module

from oscar.test.helpers import create_product
from oscar.test import ClientTestCase, patch_settings
from oscar.apps.basket.models import Basket
from oscar.apps.order.models import Order


class CheckoutMixin(object):
    fixtures = ['countries.json']

    def add_product_to_basket(self):
        product = create_product(price=D('12.00'))
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})

    def complete_guest_email_form(self, email='test@example.com'):
        response = self.client.post(reverse('checkout:index'),
                                    {'username': email,
                                     'options': 'new'})
        self.assertIsRedirect(response)

    def complete_shipping_address(self):
        response = self.client.post(reverse('checkout:shipping-address'),
                                     {'last_name': 'Doe',
                                      'line1': '1 Egg Street',
                                      'postcode': 'N1 9RT',
                                      'country': 'GB',
                                     })
        self.assertIsRedirect(response)

    def complete_shipping_method(self):
        self.client.get(reverse('checkout:shipping-method'))

    def assertRedirectUrlName(self, response, name):
        location = response['Location'].replace('http://testserver', '')
        self.assertEqual(location, reverse(name))


class DisabledAnonymousCheckoutViewsTests(ClientTestCase):
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


class EnabledAnonymousCheckoutViewsTests(ClientTestCase, CheckoutMixin):
    is_anonymous = True

    def reload_urlconf(self):
        if settings.ROOT_URLCONF in sys.modules:
            reload(sys.modules[settings.ROOT_URLCONF])
        return import_module(settings.ROOT_URLCONF)

    def add_product_to_basket(self):
        product = create_product(price=D('12.00'))
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})

    def test_shipping_address_does_require_session_email_address(self):
        with patch_settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            self.reload_urlconf()
            url = reverse('checkout:shipping-address')
            response = self.client.get(url)
            self.assertIsRedirect(response)

    def test_email_address_is_saved_with_order(self):
        with patch_settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            self.reload_urlconf()
            self.add_product_to_basket()
            self.complete_guest_email_form('barry@example.com')
            self.complete_shipping_address()
            self.complete_shipping_method()
            response = self.client.post(reverse('checkout:preview'), {'action': 'place_order'})
            response = self.client.get(reverse('checkout:thank-you'))
            order = response.context['order']
            self.assertEqual('barry@example.com', order.guest_email)


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


class ShippingMethodViewTests(ClientTestCase, CheckoutMixin):
    fixtures = ['countries.json']

    def test_shipping_method_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_redirects_by_default(self):
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')


class PaymentMethodViewTests(ClientTestCase, CheckoutMixin):

    def test_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket() 
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_view_redirects_if_no_shipping_method(self):
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-method')


class PreviewViewTests(ClientTestCase, CheckoutMixin):

    def test_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_view_redirects_if_no_shipping_method(self):
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

    def test_ok_response_if_previous_steps_complete(self):
        self.complete_shipping_address()
        self.complete_shipping_method()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsOk(response)


class PaymentDetailsViewTests(ClientTestCase, CheckoutMixin):

    def test_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.post(reverse('checkout:payment-details'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_view_redirects_if_no_shipping_method(self):
        self.add_product_to_basket()
        self.complete_shipping_address()
        response = self.client.post(reverse('checkout:payment-details'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

    def test_placing_order_with_empty_basket_redirects(self):
        self.complete_shipping_address()
        self.complete_shipping_method()
        response = self.client.post(reverse('checkout:preview'), {'action': 'place_order'})
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')


class OrderPlacementTests(ClientTestCase, CheckoutMixin):

    def setUp(self):
        Order.objects.all().delete()

        super(OrderPlacementTests, self).setUp()
        self.basket = Basket.objects.create(owner=self.user)
        self.basket.add_product(create_product(price=D('12.00')))

        self.complete_shipping_address()
        self.complete_shipping_method()
        self.response = self.client.post(reverse('checkout:preview'), {'action': 'place_order'})

    def test_placing_order_with_nonempty_basket_redirects(self):
        self.assertIsRedirect(self.response)
        self.assertRedirectUrlName(self.response, 'checkout:thank-you')

    def test_order_is_created(self):
        self.assertIsRedirect(self.response)
        orders = Order.objects.all()
        self.assertEqual(1, len(orders))
