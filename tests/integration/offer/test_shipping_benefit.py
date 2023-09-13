from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.apps.shipping.methods import FixedPrice
from oscar.apps.shipping.repository import Repository
from oscar.test import factories
from oscar.test.basket import add_product


class StubRepository(Repository):
    """
    Stubbed shipped repository which overrides the get_shipping_methods method
    in order to use a non-free default shipping method.  This allows the
    shipping discounts to be tested.
    """

    methods = [FixedPrice(D("10.00"), D("10.00"))]


class TestAnOfferWithAShippingBenefit(TestCase):
    def setUp(self):
        self.basket = factories.create_basket(empty=True)
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountCondition.objects.create(
            range=self.range, type=models.Condition.COUNT, value=1
        )
        self.benefit = models.ShippingFixedPriceBenefit.objects.create(
            type=models.Benefit.SHIPPING_FIXED_PRICE, value=D("1.00")
        )
        self.offer = models.ConditionalOffer.objects.create(
            condition=self.condition,
            benefit=self.benefit,
            offer_type=models.ConditionalOffer.SITE,
        )

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"))
        utils.Applicator().apply(self.basket)
        self.assertEqual(1, len(self.basket.offer_applications))

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("12.00"), 2)
        utils.Applicator().apply(self.basket)
        self.assertEqual(1, len(self.basket.offer_applications))

    def test_wraps_shipping_method_from_repository(self):
        add_product(self.basket, D("12.00"), 1)
        utils.Applicator().apply(self.basket)
        methods = StubRepository().get_shipping_methods(self.basket)
        method = methods[0]

        charge = method.calculate(self.basket)
        self.assertEqual(D("1.00"), charge.incl_tax)

    def test_has_discount_recorded_correctly_when_order_is_placed(self):
        add_product(self.basket, D("12.00"), 1)
        utils.Applicator().apply(self.basket)
        methods = StubRepository().get_shipping_methods(self.basket)
        method = methods[0]
        order = factories.create_order(basket=self.basket, shipping_method=method)

        discounts = order.discounts.all()
        self.assertEqual(1, len(discounts))

        discount = discounts[0]
        self.assertTrue(discount.is_shipping_discount)
        self.assertEqual(D("9.00"), discount.amount)

    def test_fixed_range_must_not_be_set(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_FIXED_PRICE,
            value=10,
            range=self.range,
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_fixed_max_affected_items_must_not_be_set(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_FIXED_PRICE,
            value=10,
            max_affected_items=5,
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_absolute_requires_value(self):
        benefit = models.Benefit(type=models.Benefit.SHIPPING_ABSOLUTE)

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_absolute_range_must_not_be_set(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_ABSOLUTE,
            value=10,
            range=self.range,
        )

        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_absolute_max_affected_items_must_not_be_set(self):
        benefit = models.Benefit(
            type=models.Benefit.SHIPPING_ABSOLUTE,
            value=10,
            max_affected_items=5,
        )

        with self.assertRaises(ValidationError):
            benefit.clean()
