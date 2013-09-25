from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar.test.factories import create_product


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
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_less_than_value(self):
        for product in [create_product(price=D('6.00'))]:
            self.basket.add_product(product, 3)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_the_same_as_value(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 4)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(4, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_more_than_value(self):
        for product in [create_product(price=D('8.00'))]:
            self.basket.add_product(product, 4)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('4.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_rounding_error_for_multiple_products(self):
        for i in range(3):
            product = create_product(price=D('7.00'))
            self.basket.add_product(product, 1)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('1.00'), result.discount)
        # Make sure discount together is the same as final discount
        # Rounding error would return 0.99 instead 1.00
        cumulative_discount = sum(
            line.discount_value for line in self.basket.all_lines())
        self.assertEqual(result.discount, cumulative_discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
