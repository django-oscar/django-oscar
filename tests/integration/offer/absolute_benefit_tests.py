from decimal import Decimal as D

from django.core import exceptions
from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar.test.factories import create_product


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
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_one_line(self):
        product = create_product(price=D('12.00'))
        self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

        # Check the discount is applied equally to each item in the line
        line = self.basket.all_lines()[0]
        prices = line.get_price_breakdown()
        self.assertEqual(1, len(prices))
        self.assertEqual(D('10.50'), prices[0][0])

    def test_applies_correctly_to_basket_which_matches_condition_with_multiple_lines(self):
        # Use a basket with 2 lines
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('12.00'))]:
            self.basket.add_product(product, 1)
        result = self.benefit.apply(self.basket, self.condition)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

        # Check the discount is applied equally to each line
        for line in self.basket.all_lines():
            self.assertEqual(D('1.50'), line._discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_multiple_lines_and_lower_total_value(self):
        # Use a basket with 2 lines
        for product in [create_product(price=D('1.00')),
                        create_product(price=D('1.50'))]:
            self.basket.add_product(product, 1)
        result = self.benefit.apply(self.basket, self.condition)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D('2.50'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('10.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount(self):
        for product in [create_product(price=D('2.00')),
                        create_product(price=D('4.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount_and_higher_prices_first(self):
        for product in [create_product(price=D('4.00')),
                        create_product(price=D('2.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAnAbsoluteDiscount(TestCase):

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
            value=D('4.00'))
        self.basket = G(Basket)

    def test_applies_correctly_when_discounts_need_rounding(self):
        # Split discount across 3 lines
        for product in [create_product(price=D('2.00')),
                        create_product(price=D('2.00')),
                        create_product(price=D('2.00'))]:
            self.basket.add_product(product)
        result = self.benefit.apply(self.basket, self.condition)

        self.assertEqual(D('4.00'), result.discount)
        # Check the discount is applied equally to each line
        line_discounts = [line._discount for line in self.basket.all_lines()]
        self.assertItemsEqual(line_discounts, [D('1.33'), D('1.33'), D('1.34')])


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
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00')),
                        create_product(price=D('10.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_with_smaller_prices_than_discount(self):
        for product in [create_product(price=D('2.00')),
                        create_product(price=D('1.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('1.00'), result.discount)
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
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('10.00'))]:
            self.basket.add_product(product, 1)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


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
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('10.00'))]:
            self.basket.add_product(product, 1)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 2)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('4.00'))]:
            self.basket.add_product(product, 3)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        for product in [create_product(price=D('5.00'))]:
            self.basket.add_product(product, 3)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition_but_with_lower_prices_than_discount(self):
        for product in [create_product(price=D('2.00'))]:
            self.basket.add_product(product, 6)
        result = self.benefit.apply(self.basket, self.condition)
        self.assertEqual(D('2.00'), result.discount)
        self.assertEqual(5, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)


class TestAnAbsoluteDiscountBenefit(TestCase):

    def test_requires_a_benefit_value(self):
        rng = models.Range.objects.create(
            name="", includes_all_products=True)
        benefit = models.Benefit.objects.create(
            type=models.Benefit.FIXED, range=rng
        )
        with self.assertRaises(exceptions.ValidationError):
            benefit.clean()
