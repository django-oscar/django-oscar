from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.apps.shipping import methods, repository
from oscar.test import factories
from oscar.test.basket import add_product


class ExcludingTax(methods.FixedPrice):
    charge_excl_tax = D("10.00")


class IncludingTax(methods.FixedPrice):
    charge_excl_tax = D("10.00")
    charge_incl_tax = D("12.00")


class TestAShippingPercentageDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.ShippingPercentageDiscountBenefit.objects.create(
            type=models.Benefit.SHIPPING_PERCENTAGE, value=50
        )
        self.offer = models.ConditionalOffer(
            condition=self.condition, benefit=self.benefit
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("12.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)
        self.assertTrue(result.affects_shipping)

    def test_applies_correctly_to_shipping_method_without_tax(self):
        add_product(self.basket, D("12.00"), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = ExcludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D("5.00"), charge.excl_tax)

    def test_applies_correctly_to_shipping_method_with_tax(self):
        add_product(self.basket, D("12.00"), 3)

        # Apply offers to basket
        utils.Applicator().apply_offers(self.basket, [self.offer])

        repo = repository.Repository()
        raw_method = IncludingTax()
        method = repo.apply_shipping_offer(self.basket, raw_method, self.offer)
        charge = method.calculate(self.basket)
        self.assertEqual(D("6.00"), charge.incl_tax)
        self.assertEqual(D("5.00"), charge.excl_tax)

    def test_shipping_percentage_required(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=None,  # This should be required
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_shipping_percentage_validation(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=105,  # Invalid value
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_shipping_range_must_not_be_set(self):
        product_range = models.Range.objects.create(
            name="Foo", includes_all_products=True
        )
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=50,
            range=product_range,  # Range shouldn't be allowed
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_shipping_max_affected_items_must_not_be_set(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_PERCENTAGE,
            value=50,
            max_affected_items=5,
        )

        with self.assertRaises(ValidationError):
            benefit.clean()
