from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, utils
from oscar.apps.shipping.repository import Repository
from oscar.apps.shipping.methods import FixedPrice
from oscar.test.basket import add_product
from oscar.test import factories


def create_offer():
    range = models.Range.objects.create(
        name="All products", includes_all_products=True)
    condition = models.CountCondition.objects.create(
        range=range,
        type=models.Condition.COUNT,
        value=1)
    benefit = models.ShippingFixedPriceBenefit.objects.create(
        type=models.Benefit.SHIPPING_FIXED_PRICE,
        value=D('1.00'))
    return models.ConditionalOffer.objects.create(
        condition=condition,
        benefit=benefit,
        offer_type=models.ConditionalOffer.SITE)


class StubRepository(Repository):
    """
    Stubbed shipped repository which overrides the get_shipping_methods method
    in order to use a non-free default shipping method.  This allows the
    shipping discounts to be tested.
    """
    methods = [FixedPrice(D('10.00'), D('10.00'))]


class TestAnOfferWithAShippingBenefit(TestCase):

    def setUp(self):
        self.basket = factories.create_basket(empty=True)
        create_offer()

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D('12.00'))
        utils.Applicator().apply(self.basket)
        self.assertEqual(1, len(self.basket.offer_applications))

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D('12.00'), 2)
        utils.Applicator().apply(self.basket)
        self.assertEqual(1, len(self.basket.offer_applications))

    def test_wraps_shipping_method_from_repository(self):
        add_product(self.basket, D('12.00'), 1)
        utils.Applicator().apply(self.basket)
        methods = StubRepository().get_shipping_methods(self.basket)
        method = methods[0]

        charge = method.calculate(self.basket)
        self.assertEqual(D('1.00'), charge.incl_tax)

    def test_has_discount_recorded_correctly_when_order_is_placed(self):
        add_product(self.basket, D('12.00'), 1)
        utils.Applicator().apply(self.basket)
        methods = StubRepository().get_shipping_methods(self.basket)
        method = methods[0]
        order = factories.create_order(basket=self.basket,
                                       shipping_method=method)

        discounts = order.discounts.all()
        self.assertEqual(1, len(discounts))

        discount = discounts[0]
        self.assertTrue(discount.is_shipping_discount)
        self.assertEqual(D('9.00'), discount.amount)
