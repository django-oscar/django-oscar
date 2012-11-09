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
        self.benefit = models.ShippingPercentageDiscountBenefit.objects.create(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=50)
        self.offer = models.ConditionalOffer(
            condition=self.condition,
            benefit=self.benefit)
        self.basket = G(Basket)

    def test_applies_correctly_to_empty_basket(self):
        discount = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertEqual(50, self.basket.shipping_offer.benefit.value)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 2)
        self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertEqual(50, self.basket.shipping_offer.benefit.value)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        for product in [create_product(price=D('12.00'))]:
            self.basket.add_product(product, 3)
        self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)
        self.assertEqual(50, self.basket.shipping_offer.benefit.value)
