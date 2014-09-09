from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.test.basket import add_product
from oscar.test.offer import add_line
from oscar.test import factories
from oscar.apps.shipping import repository, methods


class ExcludingTax(methods.FixedPrice):
    charge_excl_tax = D('10.00')


class IncludingTax(methods.FixedPrice):
    charge_excl_tax = D('10.00')
    charge_incl_tax = D('12.00')


class TestAShippingPercentageDiscount(TestCase):

    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.condition = models.NoneCondition.objects.create(
            range=range,
            type=models.Condition.NONE)
        self.benefit = models.ShippingPercentageDiscountBenefit.objects.create(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=50)
        self.offer = models.ConditionalOffer(
            condition=self.condition,
            benefit=self.benefit)
        self.basket = factories.create_basket(empty=True)
        self.set_of_lines = utils.SetOfLines([])

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.set_of_lines)
        self.assertEqual(0, result.discount)
        self.assertEqual(0, self.set_of_lines.num_items_with_benefit)
        self.assertEqual(0, self.set_of_lines.num_items_without_benefit)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_line(self.set_of_lines, D('12.00'), 2)
        result = self.benefit.apply(self.set_of_lines)
        self.assertEqual(0, self.set_of_lines.num_items_with_benefit)
        self.assertEqual(2, self.set_of_lines.num_items_without_benefit)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_line(self.set_of_lines, D('12.00'), 3)
        result = self.benefit.apply(self.set_of_lines)
        self.assertEqual(0, self.set_of_lines.num_items_with_benefit)
        self.assertEqual(3, self.set_of_lines.num_items_without_benefit)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_shipping_method_without_tax(self):
        add_product(self.basket, D('12.00'), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers_to_basket(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = ExcludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D('5.00'), charge.excl_tax)

    def test_applies_correctly_to_shipping_method_with_tax(self):
        add_product(self.basket, D('12.00'), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers_to_basket(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = IncludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D('6.00'), charge.incl_tax)
        self.assertEqual(D('5.00'), charge.excl_tax)
