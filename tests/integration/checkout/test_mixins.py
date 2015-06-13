from decimal import Decimal as D
import mock

from django.test import TestCase

from oscar.apps.checkout.calculators import OrderTotalCalculator
from oscar.apps.checkout.mixins import CheckoutSessionMixin, OrderPlacementMixin
from oscar.apps.checkout.exceptions import FailedPreCondition
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.utils import RequestFactory
from oscar.apps.shipping.methods import FixedPrice


class TestOrderPlacementMixin(TestCase):

    def test_returns_none_when_no_shipping_address_passed_to_creation_method(self):
        address = OrderPlacementMixin().create_shipping_address(
            user=mock.Mock(), shipping_address=None)
        self.assertEqual(address, None)

    def test_update_address_book(self):
        basket = factories.create_basket(empty=True)
        user = factories.UserFactory()
        add_product(basket, D('12.00'))
        shipping_method = FixedPrice(D('5.00'), D('5.00'))

        billing_address = factories.BillingAddressFactory(line1='1 Boardwalk Place',
                                                          line2='Trafalgar Way',
                                                          line3='Tower Hamlets',
                                                          line4='London')
        shipping_address = factories.ShippingAddressFactory(line1='Knightsbridge',
                                                            line2='159',
                                                            line4='London')
        shipping_charge = shipping_method.calculate(basket)
        order_total = OrderTotalCalculator().calculate(basket, shipping_charge)

        order_submission_data = {'user': user,
                                 'order_number': '12345',
                                 'basket': basket,
                                 'shipping_address': shipping_address,
                                 'shipping_method': shipping_method,
                                 'shipping_charge': shipping_charge,
                                 'billing_address': billing_address,
                                 'order_total': order_total}
        OrderPlacementMixin().place_order(**order_submission_data)

        self.assertEqual(user.addresses.filter(hash=billing_address.generate_hash()).count(), 1)
        self.assertEqual(user.addresses.filter(hash=shipping_address.generate_hash()).count(), 1)

        user_billing_address = user.addresses.get(hash=billing_address.generate_hash())
        user_shipping_address = user.addresses.get(hash=shipping_address.generate_hash())
        self.assertEqual(user_billing_address.num_orders_as_billing_address, 1)
        self.assertEqual(user_shipping_address.num_orders_as_shipping_address, 1)

        order_submission_data['order_number'] = '12346'

        OrderPlacementMixin().place_order(**order_submission_data)

        user_billing_address = user.addresses.get(hash=billing_address.generate_hash())
        user_shipping_address = user.addresses.get(hash=shipping_address.generate_hash())
        self.assertEqual(user_billing_address.num_orders_as_billing_address, 2)
        self.assertEqual(user_shipping_address.num_orders_as_shipping_address, 2)

        order_submission_data.pop('billing_address', None)
        order_submission_data['order_number'] = '123457'
        OrderPlacementMixin().place_order(**order_submission_data)

        user_billing_address = user.addresses.get(hash=billing_address.generate_hash())
        user_shipping_address = user.addresses.get(hash=shipping_address.generate_hash())
        self.assertEqual(user_billing_address.num_orders_as_billing_address, 2)
        self.assertEqual(user_shipping_address.num_orders_as_shipping_address, 3)

        shipping_address.line2 = '160'
        order_submission_data['billing_address'] = billing_address
        order_submission_data['order_number'] = '123458'
        OrderPlacementMixin().place_order(**order_submission_data)

        user_billing_address = user.addresses.get(hash=billing_address.generate_hash())
        user_shipping_address = user.addresses.get(hash=shipping_address.generate_hash())
        self.assertEqual(user_billing_address.num_orders_as_billing_address, 3)
        self.assertEqual(user_shipping_address.num_orders_as_shipping_address, 1)


class TestCheckoutSessionMixin(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.product = factories.create_product(num_in_stock=10)
        self.stock_record = self.product.stockrecords.first()

    def add_product_to_basket(self, product, quantity=1):
        self.request.basket.add_product(product, quantity=quantity)
        self.assertEquals(len(self.request.basket.all_lines()), 1)
        self.assertEquals(self.request.basket.all_lines()[0].product, product)

    def test_check_basket_is_valid_no_stock_available(self):
        self.add_product_to_basket(self.product)
        CheckoutSessionMixin().check_basket_is_valid(self.request)
        self.stock_record.allocate(10)
        self.stock_record.save()
        with self.assertRaises(FailedPreCondition):
            CheckoutSessionMixin().check_basket_is_valid(self.request)

    def test_check_basket_is_valid_stock_exceeded(self):
        self.add_product_to_basket(self.product)
        CheckoutSessionMixin().check_basket_is_valid(self.request)
        self.request.basket.add_product(self.product, quantity=11)
        with self.assertRaises(FailedPreCondition):
            CheckoutSessionMixin().check_basket_is_valid(self.request)
