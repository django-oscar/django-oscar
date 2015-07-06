from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.offer import models
from oscar.test import factories
from oscar.test.basket import add_product, add_products


class TestAPercentageDiscountAppliedWithNoneCondition(TestCase):

    def setUp(self):
        range = models.Range(
            name="All products", includes_all_products=True)
        self.condition = models.NoneCondition(
            range=range,
            type=models.Condition.NONE)
        self.benefit = models.PercentageDiscountBenefit(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20)
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_with_no_discountable_products(self):
        product = factories.create_product(is_discountable=False)
        add_product(self.basket, D('12.00'), 2, product=product)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D('12.00'), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2 * D('12.00') * D('0.2'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D('12.00'), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D('12.00') * D('0.2'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithNoneCondition(TestCase):

    def setUp(self):
        range = models.Range(
            name="All products", includes_all_products=True)
        self.condition = models.NoneCondition(
            range=range,
            type=models.Condition.NONE)
        self.benefit = models.PercentageDiscountBenefit(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1)
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D('12.00'), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D('12.00') * D('0.2'), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D('12.00'), 2), (D('20.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D('12.00') * D('0.2'), result.discount)
        # Should only consume the condition products
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)
