from decimal import Decimal as D

from django.test import TestCase
import mock

from apps.shipping import methods


class TestStandard(TestCase):

    def setUp(self):
        self.method = methods.Standard()
        self.basket = mock.Mock()

    def test_is_free_over_threshold(self):
        self.basket.total_incl_tax = D('20.00')
        price = self.method.calculate(self.basket)
        self.assertEqual(price.incl_tax, D('0.00'))

    def test_is_per_item_under_threshold(self):
        self.basket.total_incl_tax = D('10.00')
        self.basket.num_items = 3
        price = self.method.calculate(self.basket)
        self.assertEqual(
            price.incl_tax, 3 * self.method.charge_per_item)


class TestExpress(TestCase):

    def setUp(self):
        self.method = methods.Express()
        self.basket = mock.Mock()

    def test_is_per_item_under_threshold(self):
        self.basket.total_incl_tax = D('10.00')
        self.basket.num_items = 3
        price = self.method.calculate(self.basket)
        self.assertEqual(
            price.incl_tax, 3 * self.method.charge_per_item)
