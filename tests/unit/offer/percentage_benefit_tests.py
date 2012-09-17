from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product


class TestAPercentageDiscountAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=2)
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_with_no_discountable_products(self):
        for product in [create_product(price=D('12.00'))]:
            product.is_discountable = False
            product.save()
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(2 * D('12.00') * D('0.2'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(3 * D('12.00') * D('0.2'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=2)
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20,
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
        self.assertEqual(1 * D('12.00') * D('0.2'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('20.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(1 * D('12.00') * D('0.2'), discount)
        # Should only consume the condition products
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)


class TestAPercentageDiscountAppliedWithValueCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.ValueCondition.objects.create(
            range=range,
            type=models.Condition.VALUE,
            value=D('10.00'))
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(2 * D('5.00') * D('0.2'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(3 * D('5.00') * D('0.2'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(3 * D('4.00') * D('0.2'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithValueCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.ValueCondition.objects.create(
            range=range,
            type=models.Condition.VALUE,
            value=D('10.00'))
        self.benefit = models.PercentageDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(1 * D('5.00') * D('0.2'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(1 * D('5.00') * D('0.2'), discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        discount = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(1 * D('4.00') * D('0.2'), discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
