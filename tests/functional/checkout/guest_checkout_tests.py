import sys
from importlib import import_module

from django.test.utils import override_settings
from django.core.urlresolvers import clear_url_caches, reverse
from django.conf import settings
from django.utils.http import urlquote
from django.utils.six.moves import http_client
import mock

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_classes, get_model
from oscar.apps.shipping import methods
from oscar.test.testcases import WebTestCase
from oscar.test import factories
from . import CheckoutMixin

GatewayForm = get_class('checkout.forms', 'GatewayForm')
CheckoutSessionData = get_class('checkout.utils', 'CheckoutSessionData')
RedirectRequired, UnableToTakePayment, PaymentError = get_classes(
    'payment.exceptions', [
        'RedirectRequired', 'UnableToTakePayment', 'PaymentError'])
UnableToPlaceOrder = get_class('order.exceptions', 'UnableToPlaceOrder')

Basket = get_model('basket', 'Basket')
Order = get_model('order', 'Order')
User = get_user_model()

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
    clear_url_caches()


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestIndexView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestIndexView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:index'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        # Add product to basket but then remove its stock so it is not
        # purchasable.
        product = factories.ProductFactory()
        self.add_product_to_basket(product)
        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:index'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_new_customers_to_registration_page(self):
        self.add_product_to_basket()
        page = self.get(reverse('checkout:index'))

        form = page.form
        form['options'].select(GatewayForm.NEW)
        new_user_email = 'newcustomer@test.com'
        form['username'].value = new_user_email
        response = form.submit()

        expected_url = '{register_url}?next={forward}&email={email}'.format(
            register_url=reverse('customer:register'),
            forward='/checkout/shipping-address/',
            email=urlquote(new_user_email))
        self.assertRedirects(response, expected_url)

    def test_redirects_existing_customers_to_shipping_address_page(self):
        existing_user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password)
        self.add_product_to_basket()
        page = self.get(reverse('checkout:index'))
        form = page.form
        form.select('options', GatewayForm.EXISTING)
        form['username'].value = existing_user.email
        form['password'].value = self.password
        response = form.submit()
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    def test_redirects_guest_customers_to_shipping_address_page(self):
        self.add_product_to_basket()
        response = self.enter_guest_details()
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    def test_prefill_form_with_email_for_returning_guest(self):
        self.add_product_to_basket()
        email = 'forgetfulguest@test.com'
        self.enter_guest_details(email)
        page = self.get(reverse('checkout:index'))
        self.assertEqual(email, page.form['username'].value)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingAddressView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestShippingAddressView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()
        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectsTo(response, 'checkout:index')

    def test_redirects_customers_whose_basket_doesnt_require_shipping(self):
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectsTo(response, 'checkout:shipping-method')

    def test_redirects_customers_with_invalid_basket(self):
        # Add product to basket but then remove its stock so it is not
        # purchasable.
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:shipping-address'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_shows_initial_data_if_the_form_has_already_been_submitted(self):
        self.add_product_to_basket()
        self.enter_guest_details('hello@egg.com')
        self.enter_shipping_address()
        page = self.get(reverse('checkout:shipping-address'), user=self.user)
        self.assertEqual('John', page.form['first_name'].value)
        self.assertEqual('Doe', page.form['last_name'].value)
        self.assertEqual('1 Egg Road', page.form['line1'].value)
        self.assertEqual('Shell City', page.form['line4'].value)
        self.assertEqual('N12 9RT', page.form['postcode'].value)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingMethodView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestShippingMethodView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()
        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:index')

    def test_redirects_customers_whose_basket_doesnt_require_shipping(self):
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:payment-method')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_redirects_customers_when_no_shipping_methods_available(
            self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure no shipping methods available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = []

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_redirects_customers_when_only_one_shipping_method_is_available(
            self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure one shipping method available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free()]

        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:payment-method')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_shows_form_when_multiple_shipping_methods_available(
            self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure multiple shipping methods available
        method = mock.MagicMock()
        method.code = 'm'
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free(), method]
        form_page = self.get(reverse('checkout:shipping-method'))
        self.assertIsOk(form_page)

        response = form_page.forms[0].submit()
        self.assertRedirectsTo(response, 'checkout:payment-method')

    @mock.patch('oscar.apps.checkout.views.Repository')
    def test_check_user_can_submit_only_valid_shipping_method(self, mock_repo):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()
        method = mock.MagicMock()
        method.code = 'm'
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free(), method]
        form_page = self.get(reverse('checkout:shipping-method'))
        # a malicious attempt?
        form_page.forms[0]['method_code'].value = 'super-free-shipping'
        response = form_page.forms[0].submit()
        self.assertIsNotRedirect(response)
        response.mustcontain('Your submitted shipping method is not permitted')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentMethodView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPaymentMethodView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectsTo(response, 'checkout:index')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    def test_redirects_customers_who_have_skipped_shipping_method_step(self):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        response = self.get(reverse('checkout:payment-method'))
        self.assertRedirectsTo(response, 'checkout:shipping-method')


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentDetailsView(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPaymentDetailsView, self).setUp()

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_with_invalid_basket(self):
        product = factories.create_product(num_in_stock=1)
        self.add_product_to_basket(product)
        self.enter_guest_details()
        self.enter_shipping_address()

        product.stockrecords.all().update(num_in_stock=0)

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_who_have_skipped_guest_form(self):
        self.add_product_to_basket()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectsTo(response, 'checkout:index')

    def test_redirects_customers_who_have_skipped_shipping_address_form(self):
        self.add_product_to_basket()
        self.enter_guest_details()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectsTo(response, 'checkout:shipping-address')

    def test_redirects_customers_who_have_skipped_shipping_method_step(self):
        self.add_product_to_basket()
        self.enter_guest_details()
        self.enter_shipping_address()

        response = self.get(reverse('checkout:payment-details'))
        self.assertRedirectsTo(response, 'checkout:shipping-method')

    @mock.patch('oscar.apps.checkout.views.PaymentDetailsView.handle_payment')
    def test_redirects_customers_when_using_bank_gateway(self, mock_method):

        bank_url = 'https://bank-website.com'
        e = RedirectRequired(url=bank_url)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order(is_guest=True)
        bank_redirect = preview.forms['place_order_form'].submit()
        assert bank_redirect.location == bank_url

    @mock.patch('oscar.apps.checkout.views.PaymentDetailsView.handle_payment')
    def test_handles_anticipated_payments_errors_gracefully(self, mock_method):
        msg = 'Submitted expiration date is wrong'
        e = UnableToTakePayment(msg)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order(is_guest=True)
        response = preview.forms['place_order_form'].submit()
        self.assertIsOk(response)
        # check user is warned
        response.mustcontain(msg)
        # check basket is restored
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch('oscar.apps.checkout.views.logger')
    @mock.patch('oscar.apps.checkout.views.PaymentDetailsView.handle_payment')
    def test_handles_unexpected_payment_errors_gracefully(
            self, mock_method, mock_logger):
        msg = 'This gateway is down for maintenance'
        e = PaymentError(msg)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order(is_guest=True)
        response = preview.forms['place_order_form'].submit()
        self.assertIsOk(response)
        # check user is warned with a generic error
        response.mustcontain(
            'A problem occurred while processing payment for this order',
            no=[msg])
        # admin should be warned
        self.assertTrue(mock_logger.error.called)
        # check basket is restored
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch('oscar.apps.checkout.views.logger')
    @mock.patch('oscar.apps.checkout.views.PaymentDetailsView.handle_payment')
    def test_handles_bad_errors_during_payments(
            self, mock_method, mock_logger):
        e = Exception()
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order(is_guest=True)
        response = preview.forms['place_order_form'].submit()
        self.assertIsOk(response)
        self.assertTrue(mock_logger.error.called)
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch('oscar.apps.checkout.views.logger')
    @mock.patch('oscar.apps.checkout.views.PaymentDetailsView.handle_order_placement')
    def test_handles_unexpected_order_placement_errors_gracefully(
            self, mock_method, mock_logger):
        e = UnableToPlaceOrder()
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order(is_guest=True)
        response = preview.forms['place_order_form'].submit()
        self.assertIsOk(response)
        self.assertTrue(mock_logger.error.called)
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentDetailsWithPreview(CheckoutMixin, WebTestCase):
    is_anonymous = True
    csrf_checks = False

    def setUp(self):
        reload_url_conf()
        super(TestPaymentDetailsWithPreview, self).setUp()

    def test_payment_form_being_submitted_from_payment_details_view(self):
        payment_details = self.reach_payment_details_page(is_guest=True)
        preview = payment_details.forms['sensible_data'].submit()
        self.assertEqual(0, Order.objects.all().count())
        preview.form.submit().follow()
        self.assertEqual(1, Order.objects.all().count())

    def test_handles_invalid_payment_forms(self):
        payment_details = self.reach_payment_details_page(is_guest=True)
        form = payment_details.forms['sensible_data']
        # payment forms should use the preview URL not the payment details URL
        form.action = reverse('checkout:payment-details')
        self.assertEqual(form.submit(status="*").status_code, http_client.BAD_REQUEST)

@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPlacingOrder(CheckoutMixin, WebTestCase):
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super(TestPlacingOrder, self).setUp()

    def test_saves_guest_email_with_order(self):
        preview = self.ready_to_place_an_order(is_guest=True)
        thank_you = preview.forms['place_order_form'].submit().follow()
        order = thank_you.context['order']
        self.assertEqual('hello@egg.com', order.guest_email)
