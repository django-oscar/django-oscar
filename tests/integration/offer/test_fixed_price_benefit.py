from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.offer import models
from oscar.test import factories
from oscar.test.basket import add_product, add_products


class TestAFixedPriceDiscountAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=3)
        self.benefit = models.FixedPriceBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED_PRICE,
            value=D('20.00'))
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_less_than_value(self):
        add_product(self.basket, D('6.00'), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_the_same_as_value(self):
        add_product(self.basket, D('5.00'), 4)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(4, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_more_than_value(self):
        add_product(self.basket, D('8.00'), 4)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('4.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_rounding_error_for_multiple_products(self):
        add_products(self.basket,
                     [(D('7.00'), 1), (D('7.00'), 1), (D('7.00'), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('1.00'), result.discount)
        # Make sure discount together is the same as final discount
        # Rounding error would return 0.99 instead 1.00
        cumulative_discount = sum(
            line.discount_value for line in self.basket.all_lines())
        self.assertEqual(result.discount, cumulative_discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
