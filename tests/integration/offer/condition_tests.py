from decimal import Decimal as D

from django.test import TestCase
import mock

from oscar.apps.offer import models
from oscar.test import factories
from oscar.test.basket import add_product
from tests.unit.offer import OfferTest


class TestCountCondition(OfferTest):

    def setUp(self):
        super(TestCountCondition, self).setUp()
        self.condition = models.CountCondition(
            range=self.range, type="Count", value=2)
        self.offer = mock.Mock()
        self.offer.applies_to_tax_exclusive_prices = False

    def test_is_not_satified_by_empty_basket(self):
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_not_discountable_product_fails_condition(self):
        prod1, prod2 = factories.create_product(), factories.create_product()
        prod2.is_discountable = False
        prod2.save()
        add_product(self.basket, product=prod1)
        add_product(self.basket, product=prod2)
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_empty_basket_fails_partial_condition(self):
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_smaller_quantity_basket_passes_partial_condition(self):
        add_product(self.basket)
        self.assertTrue(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_smaller_quantity_basket_upsell_message(self):
        add_product(self.basket)
        self.assertTrue('Buy 1 more product from ' in
                        self.condition.get_upsell_message(self.offer, self.basket))

    def test_matching_quantity_basket_fails_partial_condition(self):
        add_product(self.basket, quantity=2)
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_matching_quantity_basket_passes_condition(self):
        add_product(self.basket, quantity=2)
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_greater_quantity_basket_passes_condition(self):
        add_product(self.basket, quantity=3)
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_consumption(self):
        add_product(self.basket, quantity=3)
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertEqual(1, self.basket.all_lines()[0].quantity_without_discount)

    def test_is_satisfied_accounts_for_consumed_items(self):
        add_product(self.basket, quantity=3)
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))


class ValueConditionTest(OfferTest):
    def setUp(self):
        super(ValueConditionTest, self).setUp()
        self.condition = models.ValueCondition(
            range=self.range, type="Value", value=D('10.00'))
        self.offer = mock.Mock()
        self.offer.applies_to_tax_exclusive_prices = False
        self.item = factories.create_product(price=D('5.00'))
        self.expensive_item = factories.create_product(price=D('15.00'))

    def test_empty_basket_fails_condition(self):
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_empty_basket_fails_partial_condition(self):
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_less_value_basket_fails_condition(self):
        add_product(self.basket, D('5'))
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_not_discountable_item_fails_condition(self):
        product = factories.create_product(is_discountable=False)
        add_product(self.basket, D('15'), product=product)
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_upsell_message(self):
        add_product(self.basket, D('5'))
        self.assertTrue('Spend' in self.condition.get_upsell_message(self.offer, self.basket))

    def test_matching_basket_fails_partial_condition(self):
        add_product(self.basket, D('5'), 2)
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_less_value_basket_passes_partial_condition(self):
        add_product(self.basket, D('5'), 1)
        self.assertTrue(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_matching_basket_passes_condition(self):
        add_product(self.basket, D('5'), 2)
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_greater_than_basket_passes_condition(self):
        add_product(self.basket, D('5'), 3)
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_consumption(self):
        add_product(self.basket, D('5'), 3)
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertEqual(1, self.basket.all_lines()[0].quantity_without_discount)

    def test_consumption_with_high_value_product(self):
        add_product(self.basket, D('15'), 1)
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertEqual(0, self.basket.all_lines()[0].quantity_without_discount)

    def test_is_consumed_respects_quantity_consumed(self):
        add_product(self.basket, D('15'), 1)
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))


class TestCoverageCondition(TestCase):

    def setUp(self):
        self.products = [factories.create_product(), factories.create_product()]
        self.range = models.Range.objects.create(name="Some products")
        for product in self.products:
            self.range.add_product(product)
            self.range.add_product(product)
        self.basket = factories.create_basket(empty=True)
        self.condition = models.CoverageCondition(
            range=self.range, type="Coverage", value=2)
        self.offer = mock.Mock()
        self.offer.applies_to_tax_exclusive_prices = False

    def test_empty_basket_fails(self):
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_empty_basket_fails_partial_condition(self):
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_single_item_fails(self):
        add_product(self.basket, product=self.products[0])
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_not_discountable_item_fails(self):
        self.products[0].is_discountable = False
        self.products[0].save()
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_single_item_passes_partial_condition(self):
        add_product(self.basket, product=self.products[0])
        self.assertTrue(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_upsell_message(self):
        add_product(self.basket, product=self.products[0])
        self.assertTrue(
            'Buy 1 more' in self.condition.get_upsell_message(self.offer, self.basket))

    def test_duplicate_item_fails(self):
        add_product(self.basket, quantity=2, product=self.products[0])
        self.assertFalse(self.condition.is_satisfied(self.offer, self.basket))

    def test_duplicate_item_passes_partial_condition(self):
        add_product(self.basket, quantity=2, product=self.products[0])
        self.assertTrue(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_covering_items_pass(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        self.assertTrue(self.condition.is_satisfied(self.offer, self.basket))

    def test_covering_items_fail_partial_condition(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        self.assertFalse(self.condition.is_partially_satisfied(self.offer, self.basket))

    def test_covering_items_are_consumed(self):
        add_product(self.basket, product=self.products[0])
        add_product(self.basket, product=self.products[1])
        self.condition.consume_items(self.offer, self.basket, [])
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_consumed_items_checks_affected_items(self):
        # Create new offer
        range = models.Range.objects.create(name="All products", includes_all_products=True)
        cond = models.CoverageCondition(range=range, type="Coverage", value=2)

        # Get 4 distinct products in the basket
        self.products.extend(
            [factories.create_product(), factories.create_product()])
        for product in self.products:
            add_product(self.basket, product=product)

        self.assertTrue(cond.is_satisfied(self.offer, self.basket))
        cond.consume_items(self.offer, self.basket, [])
        self.assertEqual(2, self.basket.num_items_without_discount)

        self.assertTrue(cond.is_satisfied(self.offer, self.basket))
        cond.consume_items(self.offer, self.basket, [])
        self.assertEqual(0, self.basket.num_items_without_discount)
