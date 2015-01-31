from __future__ import unicode_literals
from django.core.urlresolvers import reverse

from oscar.core.loading import get_model, get_class
from oscar.test.newfactories import UserAddressFactory
from oscar.test.testcases import WebTestCase
from oscar.test import factories
from . import CheckoutMixin

Order = get_model('order', 'Order')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
UserAddress = get_model('address', 'UserAddress')
GatewayForm = get_class('checkout.forms', 'GatewayForm')


class TestIndexView(CheckoutMixin, WebTestCase):

    def test_requires_login(self):
        response = self.get(reverse('checkout:index'), user=None)
        self.assertIsRedirect(response)

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:index'))
        self.assertRedirectsTo(response, 'basket:summary')

    def test_redirects_customers_to_shipping_address_view(self):
        self.add_product_to_basket()
        response = self.get(reverse('checkout:index'))
        self.assertRedirectsTo(response, 'checkout:shipping-address')


class TestShippingAddressView(CheckoutMixin, WebTestCase):

    def setUp(self):
        super(TestShippingAddressView, self).setUp()
        self.user_address = UserAddressFactory(
            user=self.user, country=self.create_shipping_country())

    def test_requires_login(self):
        response = self.get(reverse('checkout:shipping-address'), user=None)
        self.assertIsRedirect(response)

    def test_submitting_valid_form_adds_data_to_session(self):
        self.add_product_to_basket()
        page = self.get(reverse('checkout:shipping-address'))
        form = page.forms['new_shipping_address']
        form['first_name'] = 'Barry'
        form['last_name'] = 'Chuckle'
        form['line1'] = '1 King Street'
        form['line4'] = 'Gotham City'
        form['postcode'] = 'N1 7RR'
        response = form.submit()
        self.assertRedirectsTo(response, 'checkout:shipping-method')

        session_data = self.app.session['checkout_data']
        session_fields = session_data['shipping']['new_address_fields']
        self.assertEqual('Barry', session_fields['first_name'])
        self.assertEqual('Chuckle', session_fields['last_name'])
        self.assertEqual('1 King Street', session_fields['line1'])
        self.assertEqual('Gotham City', session_fields['line4'])
        self.assertEqual('N1 7RR', session_fields['postcode'])

    def test_only_shipping_address_are_shown(self):
        not_shipping_country = factories.CountryFactory(
            iso_3166_1_a2='US', name="UNITED STATES",
            is_shipping_country=False)
        not_shipping_address = UserAddressFactory(
            user=self.user, country=not_shipping_country, line4='New York')
        self.add_product_to_basket()
        page = self.get(reverse('checkout:shipping-address'))
        page.mustcontain(
            self.user_address.line4, self.user_address.country.name,
            no=[not_shipping_address.country.name, not_shipping_address.line4])

    def test_can_select_an_existing_shipping_address(self):
        self.add_product_to_basket()
        page = self.get(reverse('checkout:shipping-address'), user=self.user)
        self.assertIsOk(page)
        form = page.forms["select_shipping_address_%s" % self.user_address.id]
        response = form.submit()
        self.assertRedirectsTo(response, 'checkout:shipping-method')


class TestUserAddressUpdateView(CheckoutMixin, WebTestCase):

    def setUp(self):
        country = self.create_shipping_country()
        super(TestUserAddressUpdateView, self).setUp()
        self.user_address = UserAddressFactory(user=self.user, country=country)

    def test_requires_login(self):
        response = self.get(
            reverse('checkout:user-address-update',
                    kwargs={'pk': self.user_address.pk}),
            user=None)
        self.assertIsRedirect(response)

    def test_submitting_valid_form_modifies_user_address(self):
        page = self.get(
            reverse(
                'checkout:user-address-update',
                kwargs={'pk': self.user_address.pk}),
            user=self.user)

        form = page.forms['update_user_address']
        form['first_name'] = 'Tom'
        response = form.submit()
        self.assertRedirectsTo(response, 'checkout:shipping-address')
        self.assertEqual('Tom', UserAddress.objects.get().first_name)


class TestShippingMethodView(CheckoutMixin, WebTestCase):

    def test_requires_login(self):
        response = self.get(reverse('checkout:shipping-method'), user=None)
        self.assertIsRedirect(response)

    def test_redirects_when_only_one_shipping_method(self):
        self.add_product_to_basket()
        self.enter_shipping_address()
        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectsTo(response, 'checkout:payment-method')


class TestDeleteUserAddressView(CheckoutMixin, WebTestCase):

    def setUp(self):
        super(TestDeleteUserAddressView, self).setUp()
        self.country = self.create_shipping_country()
        self.user_address = UserAddressFactory(
            user=self.user, country=self.country)

    def test_requires_login(self):
        response = self.get(
            reverse('checkout:user-address-delete',
                    kwargs={'pk': self.user_address.pk}),
            user=None)
        self.assertIsRedirect(response)

    def test_can_delete_a_user_address_from_shipping_address_page(self):
        self.add_product_to_basket()
        page = self.get(reverse('checkout:shipping-address'), user=self.user)
        delete_confirm = page.click(
            href=reverse('checkout:user-address-delete',
                         kwargs={'pk': self.user_address.pk}))
        form = delete_confirm.forms["delete_address_%s" % self.user_address.id]
        form.submit()

        # Ensure address is deleted
        user_addresses = UserAddress.objects.filter(user=self.user)
        self.assertEqual(0, len(user_addresses))


class TestPreviewView(CheckoutMixin, WebTestCase):

    def test_allows_order_to_be_placed(self):
        self.add_product_to_basket()
        self.enter_shipping_address()

        payment_details = self.get(
            reverse('checkout:shipping-method')).follow().follow()
        preview = payment_details.click(linkid="view_preview")
        preview.forms['place_order_form'].submit().follow()

        self.assertEqual(1, Order.objects.all().count())


class TestPlacingAnOrderUsingAVoucher(CheckoutMixin, WebTestCase):

    def test_records_use(self):
        self.add_product_to_basket()
        self.add_voucher_to_basket()
        self.enter_shipping_address()
        thankyou = self.place_order()

        order = thankyou.context['order']
        self.assertEqual(1, order.discounts.all().count())

        discount = order.discounts.all()[0]
        voucher = discount.voucher
        self.assertEqual(1, voucher.num_orders)


class TestPlacingAnOrderUsingAnOffer(CheckoutMixin, WebTestCase):

    def test_records_use(self):
        offer = factories.create_offer()
        self.add_product_to_basket()
        self.enter_shipping_address()
        self.place_order()

        # Reload offer
        offer = ConditionalOffer.objects.get(id=offer.id)

        self.assertEqual(1, offer.num_orders)
        self.assertEqual(1, offer.num_applications)
