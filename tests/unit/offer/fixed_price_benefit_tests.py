from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar_testsupport.factories import create_product


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
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_less_than_value(self):
        for product in [create_product(price=D('6.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_the_same_as_value(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 4)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(4, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_more_than_value(self):
        for product in [create_product(price=D('8.00'))]:
            self.basket.add_product(product, 4)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('4.00'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)
