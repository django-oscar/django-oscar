from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models
from oscar.test.basket import add_product, add_products
from oscar.test import factories


class TestACountConditionWithPercentageDiscount(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        condition = models.CountCondition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=3)
        benefit = models.PercentageDiscountBenefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1)
        self.offer = models.ConditionalOffer(
            name="Test",
            offer_type=models.ConditionalOffer.SITE,
            condition=condition,
            benefit=benefit)

    def test_consumes_correct_number_of_products_for_3_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D('1'), 3)

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(0, basket.num_items_without_discount)
        self.assertFalse(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_4_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_products(basket, [(D('1'), 2), (D('1'), 2)])

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(1, basket.num_items_without_discount)
        self.assertFalse(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_6_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_products(basket, [(D('1'), 3), (D('1'), 3)])

        # First application
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(3, basket.num_items_without_discount)

        # Second application
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(6, basket.num_items_with_discount)
