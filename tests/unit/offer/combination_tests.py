from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar_testsupport.factories import create_product


class TestACountConditionWithPercentageDiscount(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        condition = models.Condition.objects.create(
            range=range,
            type=models.Condition.COUNT,
            value=3)
        benefit = models.Benefit.objects.create(
            range=range,
            type=models.Benefit.PERCENTAGE,
            value=20,
            max_affected_items=1)
        self.offer = models.ConditionalOffer.objects.create(
            name="Test",
            offer_type=models.ConditionalOffer.SITE,
            condition=condition,
            benefit=benefit)

    def test_consumes_correct_number_of_products_for_3_product_basket(self):
        basket = G(Basket)
        for product in [create_product()]:
            basket.add_product(product, 3)

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(0, basket.num_items_without_discount)
        self.assertFalse(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_4_product_basket(self):
        basket = G(Basket)
        for product in [create_product(), create_product()]:
            basket.add_product(product, 2)

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(1, basket.num_items_without_discount)
        self.assertFalse(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_6_product_basket(self):
        basket = G(Basket)
        for product in [create_product(), create_product()]:
            basket.add_product(product, 3)

        # First application
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount > 0)
        self.assertEqual(3, basket.num_items_with_discount)
        self.assertEqual(3, basket.num_items_without_discount)

        # Second application
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount > 0)
        self.assertEqual(6, basket.num_items_with_discount)
