from decimal import Decimal as D

from django.test import TestCase
from django.test.utils import override_settings

from oscar.apps.basket.models import Basket
from oscar.apps.offer import models
from oscar.apps.partner import strategy
from oscar.test.basket import add_product


def create_fixed_tax_basket(price):
    basket = Basket.objects.create()
    basket.strategy = strategy.UK()
    add_product(basket, D(price), 1)
    return basket


class TestBasketTotalAfterRounding(TestCase):
    def setUp(self):
        product_range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        condition = models.CountCondition.objects.create(
            range=product_range, type=models.Condition.COUNT, value=1
        )
        self.benefit = models.Benefit.objects.create(
            range=product_range,
            type=models.Benefit.FIXED,
            value=D("11.45"),
        )
        self.offer = models.ConditionalOffer(
            name="Test",
            offer_type=models.ConditionalOffer.SITE,
            condition=condition,
            benefit=self.benefit,
        )

    @override_settings(OSCAR_OFFERS_INCL_TAX=True)
    def test_total_excl_tax_precision_down(self):
        basket = create_fixed_tax_basket(9.99)
        self.benefit.value = D("4.13")
        self.offer.apply_benefit(basket)

        # 9.99-round(3.441) => 9.99-3.44 = 6.55
        self.assertEqual(basket.total_excl_tax, D("6.55"))

    @override_settings(OSCAR_OFFERS_INCL_TAX=True)
    def test_total_excl_tax_precision_up(self):
        basket = create_fixed_tax_basket(9.99)
        self.benefit.value = D("4.14")
        self.offer.apply_benefit(basket)

        # 9.99-round(3.449) => 9.99-3.45 = 6.54
        self.assertEqual(basket.total_excl_tax, D("6.54"))

    def test_total_incl_tax_precision_down(self):
        basket = create_fixed_tax_basket(20.37)
        self.offer.apply_benefit(basket)

        # 10.704 rounded to 10.70
        self.assertEqual(basket.total_incl_tax, D("10.70"))

    def test_total_incl_tax_precision_up(self):
        basket = create_fixed_tax_basket(20.38)
        self.offer.apply_benefit(basket)

        # 10.716 rounded to 10.72
        self.assertEqual(basket.total_incl_tax, D("10.72"))
