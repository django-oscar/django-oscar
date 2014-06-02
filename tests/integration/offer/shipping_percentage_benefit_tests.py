from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.test.basket import add_product
from oscar.test import factories
from oscar.apps.shipping import repository, methods


class ExcludingTax(methods.FixedPrice):
    charge_excl_tax = D('10.00')


class IncludingTax(methods.FixedPrice):
    charge_excl_tax = D('10.00')
    charge_incl_tax = D('12.00')


class TestAShippingPercentageDiscountAppliedWithCountCondition(TestCase):

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
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D('0.00'), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D('12.00'), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D('12.00'), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_shipping_method_without_tax(self):
        add_product(self.basket, D('12.00'), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = ExcludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D('5.00'), charge.excl_tax)

    def test_applies_correctly_to_shipping_method_with_tax(self):
        add_product(self.basket, D('12.00'), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = IncludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D('6.00'), charge.incl_tax)
        self.assertEqual(D('5.00'), charge.excl_tax)
