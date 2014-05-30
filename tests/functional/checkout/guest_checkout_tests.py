import sys

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.importlib import import_module
import mock
from oscar.apps.shipping import methods

from oscar.test.testcases import WebTestCase
from oscar.test import factories
from . import CheckoutMixin

# Python 3 compat
try:
    from imp import reload
except ImportError:
    pass


def reload_url_conf():
    # Reload URLs to pick up the overridden settings
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])
    import_module(settings.ROOT_URLCONF)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestIndexView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestIndexView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:index'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        # Add product to basket but then remove its stock so it is not
        # purchasable.
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:index'))
        self.assertRedirectUrlName(response, 'basket:summary')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingAddressView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestShippingAddressView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()
        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'checkout:index')

    def test_redirects_customers_whose_basket_doesnt_require_shipping(self):
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')

    def test_redirects_customers_with_invalid_basket(self):
        # Add product to basket but then remove its stock so it is not
        # purchasable.
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectUrlName(response, 'basket:summary')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingMethodView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestShippingMethodView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()
        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:index')

    def test_redirects_customers_whose_basket_doesnt_require_shipping(self):
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_redirects_customers_when_no_shipping_methods_available(self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure no shipping methods available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = []

        response = self.get(reverse('checkout:shipping-address'))
        self.assertIsOk(response)

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_redirects_customers_when_only_one_shipping_method_is_available(self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure one shipping method available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free()]

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_shows_form_when_multiple_shipping_methods_available(self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure multiple shipping methods available
        method = mock.MagicMock()
        method.code = 'm'
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [method, method]

        response = self.get(reverse('checkout:shipping-method'))
        self.assertIsOk(response)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentMethodView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPaymentMethodView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'checkout:index')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_redirects_customers_who_have_skipped_shipping_method_step(self):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectUrlName(response, 'checkout:shipping-method')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentDetailsView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPaymentDetailsView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'checkout:index')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'checkout:shipping-address')

    def test_redirects_customers_who_have_skipped_shipping_method_step(self):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectUrlName(response, 'checkout:shipping-method')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPlacingOrder(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPlacingOrder, self).setUp()

    def test_saves_guest_email_with_order(self):
        self.add_product_to_basket()
        self.enter_guest_details('hello@egg.com')
        self.enter_shipping_address()

        page = self.get(reverse('checkout:shipping-method')).follow().follow()
        preview = page.click(linkid="view_preview")
        thank_you = preview.forms['place_order_form'].submit().follow()

        order = thank_you.context['order']
        self.assertEqual('hello@egg.com', order.guest_email)
