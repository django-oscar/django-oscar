from decimal import Decimal as D
import sys

from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module
from django.test.utils import override_settings

from oscar.test.factories import (
    create_product, create_voucher, create_offer)
from oscar.test.testcases import WebTestCase
from oscar.apps.basket.models import Basket
from oscar.apps.order.models import Order
from oscar.apps.address.models import Country
from oscar.apps.voucher.models import Voucher
from oscar.apps.offer.models import ConditionalOffer
from oscar.test.basket import add_product

# Python 3 compat
try:
    from imp import reload
except ImportError:
    pass


class CheckoutMixin(object):

    def add_product_to_basket(self):
        product = create_product(price=D('12.00'), num_in_stock=10)
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})

    def add_voucher_to_basket(self, voucher=None):
        if voucher is None:
            voucher = create_voucher()
        self.client.post(reverse('basket:vouchers-add'),
                         {'code': voucher.code})

    def complete_guest_email_form(self, email='test@example.com'):
        response = self.client.post(reverse('checkout:index'),
                                    {'username': email,
                                     'options': 'new'})
        self.assertIsRedirect(response)

    def complete_shipping_address(self):
        Country.objects.get_or_create(
            iso_3166_1_a2='GB',
            is_shipping_country=True
        )
        response = self.client.post(reverse('checkout:shipping-address'),
                                     {'last_name': 'Doe',
                                      'first_name': 'John',
                                      'line1': '1 Egg Street',
                                      'line4': 'City',
                                      'postcode': 'N1 9RT',
                                      'country': 'GB',
                                     })
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

    def complete_shipping_method(self):
        self.client.get(reverse('checkout:shipping-method'))

    def submit(self):
        return self.client.post(reverse('checkout:preview'), {'action': 'place_order'})


class DisabledAnonymousCheckoutViewsTests(WebTestCase):
    is_anonymous = True

    def test_index_does_require_login(self):
        url = reverse('checkout:index')
        response = self.client.get(url)
        self.assertIsRedirect(response)

    def test_user_address_views_require_a_login(self):
        urls = [reverse('checkout:user-address-update', kwargs={'pk': 1}),
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


class EnabledAnonymousCheckoutViewsTests(WebTestCase, CheckoutMixin):
    is_anonymous = True

    def reload_urlconf(self):
        if settings.ROOT_URLCONF in sys.modules:
            reload(sys.modules[settings.ROOT_URLCONF])
        return import_module(settings.ROOT_URLCONF)

    def add_product_to_basket(self):
        product = create_product(price=D('12.00'), num_in_stock=10)
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})

    def test_shipping_address_does_require_session_email_address(self):
        with override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            self.reload_urlconf()
            url = reverse('checkout:shipping-address')
            response = self.client.get(url)
            self.assertIsRedirect(response)

    def test_email_address_is_saved_with_order(self):
        with override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True):
            self.reload_urlconf()
            self.add_product_to_basket()
            self.complete_guest_email_form('barry@example.com')
            self.complete_shipping_address()
            self.complete_shipping_method()
            response = self.client.post(reverse('checkout:preview'), {'action': 'place_order'})
            response = self.client.get(reverse('checkout:thank-you'))
            order = response.context['order']
            self.assertEqual('barry@example.com', order.guest_email)


class TestShippingAddressView(WebTestCase, CheckoutMixin):
    fixtures = ['countries.json']

    def test_pages_returns_200(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:shipping-address'))
        self.assertIsOk(response)

    def test_anon_checkout_disabled_by_default(self):
        self.assertFalse(settings.OSCAR_ALLOW_ANON_CHECKOUT)

    def test_create_shipping_address_adds_address_to_session(self):
        response = self.client.post(reverse('checkout:shipping-address'),
                                            {'last_name': 'Doe',
                                             'first_name': 'John',
                                             'line1': '1 Egg Street',
                                             'line4': 'City',
                                             'postcode': 'N1 9RT',
                                             'country': 'GB',
                                            })
        self.assertIsRedirect(response)
        session_address = self.client.session['checkout_data']['shipping']['new_address_fields']
        self.assertEqual('Doe', session_address['last_name'])
        self.assertEqual('1 Egg Street', session_address['line1'])
        self.assertEqual('N1 9RT', session_address['postcode'])

    def test_invalid_shipping_address_fails(self):
        response = self.client.post(reverse('checkout:shipping-address'),
                                    {'last_name': 'Doe',
                                     'first_name': 'John',
                                     'postcode': 'N1 9RT',
                                     'country': 'GB',
                                     })
        self.assertIsOk(response)  # no redirect


    def test_user_must_have_a_nonempty_basket(self):
        response = self.client.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'basket:summary')


class TestShippingMethodView(WebTestCase, CheckoutMixin):
    fixtures = ['countries.json']

    def test_shipping_method_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_redirects_by_default(self):
        self.add_product_to_basket()
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')

    def test_user_must_have_a_nonempty_basket(self):
        response = self.client.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'basket:summary')


class TestPaymentMethodView(WebTestCase, CheckoutMixin):

    def test_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_view_redirects_if_no_shipping_method(self):
        self.add_product_to_basket()
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

    def test_user_must_have_a_nonempty_basket(self):
        response = self.client.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'basket:summary')


class TestPreviewView(WebTestCase, CheckoutMixin):

    def test_user_must_have_a_nonempty_basket(self):
        response = self.client.get(reverse('checkout:preview'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_view_redirects_if_no_shipping_address(self):
        self.add_product_to_basket()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_view_redirects_if_no_shipping_method(self):
        self.add_product_to_basket()
        self.complete_shipping_address()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

    def test_ok_response_if_previous_steps_complete(self):
        self.add_product_to_basket()
        self.complete_shipping_address()
        self.complete_shipping_method()
        response = self.client.get(reverse('checkout:preview'))
        self.assertIsOk(response)


class TestPaymentDetailsView(WebTestCase, CheckoutMixin):

    def test_user_must_have_a_nonempty_basket(self):
        response = self.client.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'basket:summary')

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
        response = self.client.post(reverse('checkout:preview'), {'action': 'place_order'})
        self.assertIsRedirect(response)
        self.assertRedirectUrlName(response, 'basket:summary')


class TestOrderPlacement(WebTestCase, CheckoutMixin):

    def setUp(self):
        super(TestOrderPlacement, self).setUp()
        self.basket = Basket.objects.create(owner=self.user)
        add_product(self.basket, D('12.00'))

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


class TestPlacingOrderUsingAVoucher(WebTestCase, CheckoutMixin):

    def setUp(self):
        super(TestPlacingOrderUsingAVoucher, self).setUp()
        self.add_product_to_basket()
        voucher = create_voucher()
        self.add_voucher_to_basket(voucher)
        self.complete_shipping_address()
        self.complete_shipping_method()
        self.response = self.submit()

        # Reload voucher
        self.voucher = Voucher.objects.get(id=voucher.id)

    def test_is_successful(self):
        self.assertRedirectUrlName(self.response, 'checkout:thank-you')

    def test_records_use(self):
        self.assertEqual(1, self.voucher.num_orders)

    def test_records_discount(self):
        self.assertEqual(1, self.voucher.num_orders)



class TestPlacingOrderUsingAnOffer(WebTestCase, CheckoutMixin):

    def setUp(self):
        super(TestPlacingOrderUsingAnOffer, self).setUp()
        offer = create_offer()
        self.add_product_to_basket()
        self.complete_shipping_address()
        self.complete_shipping_method()
        self.response = self.submit()

        # Reload offer
        self.offer = ConditionalOffer.objects.get(id=offer.id)

    def test_is_successful(self):
        self.assertRedirectUrlName(self.response, 'checkout:thank-you')

    def test_records_use(self):
        self.assertEqual(1, self.offer.num_orders)
        self.assertEqual(1, self.offer.num_applications)
