from django.core.urlresolvers import reverse

from oscar.test.testcases import WebTestCase
from oscar.test import factories
from oscar.apps.order.models import Order
from oscar.apps.offer.models import ConditionalOffer
from . import CheckoutMixin


class TestIndexView(CheckoutMixin, WebTestCase):

    def test_requires_login(self):
        response = self.get(reverse('checkout:index'), user=None)
        self.assertIsRedirect(response)

    def test_redirects_customers_with_empty_basket(self):
        response = self.get(reverse('checkout:index'))
        self.assertRedirectUrlName(response, 'basket:summary')

    def test_redirects_customers_to_shipping_address_view(self):
        self.add_product_to_basket()
        response = self.get(reverse('checkout:index'))
        self.assertRedirectUrlName(response, 'checkout:shipping-address')


class TestShippingAddressView(CheckoutMixin, WebTestCase):

    def setUp(self):
        self.create_shipping_country()
        super(TestShippingAddressView, self).setUp()

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
        self.assertRedirectUrlName(response, 'checkout:shipping-method')

        session_data = self.app.session['checkout_data']
        session_fields = session_data['shipping']['new_address_fields']
        self.assertEqual(u'Barry', session_fields['first_name'])
        self.assertEqual(u'Chuckle', session_fields['last_name'])
        self.assertEqual(u'1 King Street', session_fields['line1'])
        self.assertEqual(u'Gotham City', session_fields['line4'])
        self.assertEqual(u'N1 7RR', session_fields['postcode'])


class TestShippingMethodView(CheckoutMixin, WebTestCase):

    def test_requires_login(self):
        response = self.get(reverse('checkout:shipping-method'), user=None)
        self.assertIsRedirect(response)

    def test_redirects_when_only_one_shipping_method(self):
        self.add_product_to_basket()
        self.enter_shipping_address()
        response = self.get(reverse('checkout:shipping-method'))
        self.assertRedirectUrlName(response, 'checkout:payment-method')


class TestPreviewView(CheckoutMixin, WebTestCase):

    def test_allows_order_to_be_placed(self):
        self.add_product_to_basket()
        self.enter_shipping_address()

        payment_details = self.get(
            reverse('checkout:shipping-method')).follow().follow()
        preview = payment_details.click(linkid="view_preview")
        preview.forms['place_order_form'].submit().follow()

        self.assertEqual(1, Order.objects.all().count())
        
    def test_allows_order_with_options_to_be_placed(self):
        self.add_product_with_option_to_basket()
        self.enter_shipping_address()

        payment_details = self.get(
        reverse('checkout:shipping-method')).follow().follow()
        preview = payment_details.click(linkid="view_preview")
        preview.forms['place_order_form'].submit().follow()
        
        orders = Order.objects.all()
        self.assertEqual(1, orders.count())    
        order = orders[0]
        lines = order.lines.all()
        self.assertEqual(1, lines.count())
        line = lines[0]
        attributes = line.attributes.all()
        self.assertEqual(1, attributes.count())


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
