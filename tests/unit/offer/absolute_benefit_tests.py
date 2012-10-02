from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product


class TestAnAbsoluteDiscountAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=2)
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED,
            value=D('3.00'))
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('10.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount(self):
        for product in [create_product(price=D('2.00')),
                        create_product(price=D('4.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount_and_higher_prices_first(self):
        for product in [create_product(price=D('4.00')),
                        create_product(price=D('2.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)


class TestAnAbsoluteDiscountWithMaxItemsSetAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=2)
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED,
            value=D('3.00'),
            max_affected_items=1)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('10.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_with_smaller_prices_than_discount(self):
        for product in [create_product(price=D('2.00')),
                        create_product(price=D('1.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('1.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)


class TestAnAbsoluteDiscountAppliedWithValueCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.ValueCondition.objects.create(
            range=range,
            type=models.Condition.VALUE,
            value=D('10.00'))
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED,
            value=D('3.00'))
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('10.00'))]:
            self.basket.add_product(product, 1)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)


class TestAnAbsoluteDiscountWithMaxItemsSetAppliedWithValueCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.ValueCondition.objects.create(
            range=range,
            type=models.Condition.VALUE,
            value=D('10.00'))
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED,
            value=D('3.00'),
            max_affected_items=1)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('10.00'))]:
            self.basket.add_product(product, 1)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition_but_with_lower_prices_than_discount(self):
        for product in [create_product(price=D('2.00'))]:
            self.basket.add_product(product, 6)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('2.00'), discount)
        self.assertEqual(5, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)
