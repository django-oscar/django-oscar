from decimal import Decimal as D

from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.basket.models import Basket
from oscar.apps.offer import models
from oscar.apps.partner import strategy
from oscar.test.basket import add_product
from oscar.test.factories import create_order


class TestAValueBasedOffer(TestCase):
    def setUp(self):
        # Get 20% if spending more than 20.00
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        condition = models.Condition.objects.create(
            range=product_range, type=models.Condition.VALUE, value=D("10.00")
        )
        benefit = models.Benefit.objects.create(
            range=product_range, type=models.Benefit.PERCENTAGE, value=20
        )
        self.offer = models.ConditionalOffer.objects.create(
            name="Test",
            offer_type=models.ConditionalOffer.SITE,
            condition=condition,
            benefit=benefit,
        )
        self.basket = Basket.objects.create()

    def test_respects_effective_price_when_taxes_not_known(self):
        # Assign US style strategy (no tax known)
        self.basket.strategy = strategy.US()

        # Add sufficient products to meet condition
        add_product(self.basket, price=D("6"), quantity=2)

        # Ensure discount is correct
        result = self.offer.apply_benefit(self.basket)
        self.assertEqual(D("2.40"), result.discount)

    def test_respects_effective_price_when_taxes_are_known(self):
        # Assign UK style strategy (20% tax)
        self.basket.strategy = strategy.UK()

        # Add sufficient products to meet condition
        add_product(self.basket, price=D("10"), quantity=2)

        # Ensure discount is calculated against tax-inclusive price
        result = self.offer.apply_benefit(self.basket)
        self.assertEqual(2 * D("10.00") * D("1.2") * D("0.20"), result.discount)
        order = create_order(basket=self.basket)
        self.assertEqual(order.basket_total_before_discounts_excl_tax, D("20"))
        self.assertEqual(order.basket_total_before_discounts_incl_tax, D("24"))

        self.assertEqual(order.total_before_discounts_incl_tax, D("24"))
        self.assertEqual(order.total_before_discounts_excl_tax, D("20"))

        self.assertEqual(order.total_discount_excl_tax, D("4.8"))
        self.assertEqual(order.total_discount_incl_tax, D("5.76"))

    @override_settings(OSCAR_OFFERS_INCL_TAX=True)
    def test_respects_effective_price_when_taxes_are_known_and_offer_is_tax_inclusive(
        self,
    ):
        self.basket.strategy = strategy.UK()
        add_product(self.basket, price=D("10"), quantity=2)

        result = self.offer.apply_benefit(self.basket)
        self.assertEqual(2 * D("10.00") * D("1.2") * D("0.20"), result.discount)
        order = create_order(basket=self.basket)

        self.assertEqual(order.total_before_discounts_incl_tax, D("24"))
        self.assertEqual(order.total_before_discounts_excl_tax, D("20"))

        self.assertEqual(order.total_discount_excl_tax, D("4"))
        self.assertEqual(order.total_discount_incl_tax, D("4.8"))
