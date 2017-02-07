import mock

from django.test import TestCase

from oscar.apps.checkout.mixins import CheckoutSessionMixin, OrderPlacementMixin
from oscar.apps.checkout.exceptions import FailedPreCondition
from oscar.test import factories
from oscar.test.utils import RequestFactory


class TestOrderPlacementMixin(TestCase):

    def test_returns_none_when_no_shipping_address_passed_to_creation_method(self):
        address = OrderPlacementMixin().create_shipping_address(
            user=mock.Mock(), shipping_address=None)
        self.assertEqual(address, None)


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
