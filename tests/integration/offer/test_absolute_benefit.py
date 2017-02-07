from decimal import Decimal as D

from django.core import exceptions
from django.test import TestCase
import mock

from oscar.apps.offer import models
from oscar.apps.offer.utils import Applicator
from oscar.test.basket import add_product, add_products
from oscar.test import factories


class TestAnAbsoluteDiscountAppliedWithCountConditionOnDifferentRange(TestCase):

    def setUp(self):
        self.condition_product = factories.ProductFactory()
        condition_range = factories.RangeFactory()
        condition_range.add_product(self.condition_product)
        self.condition = models.CountCondition.objects.create(
            range=condition_range,
            type=models.Condition.COUNT,
            value=2)

        self.benefit_product = factories.ProductFactory()
        benefit_range = factories.RangeFactory()
        benefit_range.add_product(self.benefit_product)
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=benefit_range,
            type=models.Benefit.FIXED,
            value=D('3.00'))

        self.offer = models.ConditionalOffer(
            id=1, condition=self.condition, benefit=self.benefit)
        self.basket = factories.create_basket(empty=True)

        self.applicator = Applicator()

    def test_succcessful_application_consumes_correctly(self):
        add_product(self.basket, product=self.condition_product, quantity=2)
        add_product(self.basket, product=self.benefit_product, quantity=1)

        self.applicator.apply_offers(self.basket, [self.offer])

        discounts = self.basket.offer_applications.offer_discounts
        self.assertEqual(len(discounts), 1)
        self.assertEqual(discounts[0]['freq'], 1)

    def test_condition_is_consumed_correctly(self):
        # Testing an error case reported on the mailing list
        add_product(self.basket, product=self.condition_product, quantity=3)
        add_product(self.basket, product=self.benefit_product, quantity=2)

        self.applicator.apply_offers(self.basket, [self.offer])

        discounts = self.basket.offer_applications.offer_discounts
        self.assertEqual(len(discounts), 1)
        self.assertEqual(discounts[0]['freq'], 1)


class TestAnAbsoluteDiscountAppliedWithCountCondition(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=2)
        self.offer = mock.Mock()
        self.benefit = models.AbsoluteDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.FIXED,
            value=D('3.00'))
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition_with_one_line(self):
        add_product(self.basket, price=D('12.00'), quantity=2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
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
        add_products(self.basket, [
            (D('12.00'), 1), (D('12.00'), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

        # Check the discount is applied equally to each line
        for line in self.basket.all_lines():
            self.assertEqual(D('1.50'), line.discount_value)

    def test_applies_correctly_to_basket_which_matches_condition_with_multiple_lines_and_lower_total_value(self):
        # Use a basket with 2 lines
        add_products(self.basket, [
            (D('1.00'), 1), (D('1.50'), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertTrue(result.is_successful)
        self.assertFalse(result.is_final)
        self.assertEqual(D('2.50'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [
            (D('12.00'), 2), (D('10.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount(self):
        add_products(self.basket, [
            (D('2.00'), 2), (D('4.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(4, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_with_smaller_prices_than_discount_and_higher_prices_first(self):
        add_products(self.basket, [
            (D('2.00'), 2), (D('4.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
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
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_when_discounts_need_rounding(self):
        # Split discount across 3 lines
        for price in [D('2.00'), D('2.00'), D('2.00')]:
            add_product(self.basket, price)
        result = self.benefit.apply(self.basket, self.condition, self.offer)

        self.assertEqual(D('4.00'), result.discount)
        # Check the discount is applied equally to each line
        line_discounts = [line.discount_value for line in self.basket.all_lines()]
        self.assertEqual(len(line_discounts), 3)
        for i, v in enumerate([D('1.33'), D('1.33'), D('1.34')]):
            self.assertEqual(line_discounts[i], v)


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
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D('12.00'), 2), (D('10.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_with_smaller_prices_than_discount(self):
        add_products(self.basket, [(D('2.00'), 2), (D('1.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
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
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D('10.00'), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D('5.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D('4.00'), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        add_products(self.basket, [(D('5.00'), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
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
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_single_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D('10.00'), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition(self):
        add_products(self.basket, [(D('5.00'), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D('4.00'), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_exceeds_condition_but_matches_boundary(self):
        add_products(self.basket, [(D('5.00'), 3)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('3.00'), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_multi_item_basket_which_matches_condition_but_with_lower_prices_than_discount(self):
        add_products(self.basket, [(D('2.00'), 6)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
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
