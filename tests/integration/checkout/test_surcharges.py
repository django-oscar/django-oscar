from decimal import Decimal as D

from django.test import TestCase

from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.basket import add_product

SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")


class TestSurcharges(TestCase):
    def setUp(self):
        self.applicator = SurchargeApplicator()
        self.basket = factories.create_basket(empty=True)

    def test_stock_surcharges(self):
        add_product(self.basket, D('12.00'))
        surcharges = self.applicator.get_applicable_surcharges(self.basket)

        self.assertEqual(surcharges.total.excl_tax, D('20.0'))
        self.assertEqual(surcharges.total.incl_tax, D('22.0'))
