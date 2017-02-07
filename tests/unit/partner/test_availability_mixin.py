from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.partner import strategy, availability


class TestStockRequiredMixin(TestCase):

    def setUp(self):
        self.mixin = strategy.StockRequired()
        self.product = mock.Mock()
        self.stockrecord = mock.Mock()
        self.stockrecord.price_excl_tax = D('12.00')

    def test_returns_unavailable_without_stockrecord(self):
        policy = self.mixin.availability_policy(
            self.product, None)
        self.assertIsInstance(policy, availability.Unavailable)

    def test_returns_available_when_product_class_doesnt_track_stock(self):
        product_class = mock.Mock(track_stock=False)
        self.product.get_product_class = mock.Mock(return_value=product_class)
        policy = self.mixin.availability_policy(
            self.product, self.stockrecord)
        self.assertIsInstance(policy, availability.Available)

    def test_returns_stockrequired_when_product_class_does_track_stock(self):
        product_class = mock.Mock(track_stock=True)
        self.product.get_product_class = mock.Mock(return_value=product_class)
        policy = self.mixin.availability_policy(
            self.product, self.stockrecord)
        self.assertIsInstance(policy, availability.StockRequired)
