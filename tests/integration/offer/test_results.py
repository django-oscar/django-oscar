from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, results
from oscar.test.factories import ConditionalOfferFactory, VoucherFactory


class TestOfferApplicationsObject(TestCase):
    def setUp(self):
        self.applications = results.OfferApplications()
        self.offer = models.ConditionalOffer()

    def test_is_countable(self):
        self.assertEqual(0, len(self.applications))

    def test_can_filter_shipping_discounts(self):
        result = models.ShippingDiscount()
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.shipping_discounts))

    def test_can_filter_offer_discounts(self):
        result = models.BasketDiscount(D("2.00"))
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.offer_discounts))

    def test_can_filter_post_order_actions(self):
        result = models.PostOrderAction("Something will happen")
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.post_order_actions))

    def test_grouped_voucher_discounts(self):
        voucher = VoucherFactory()
        offer1 = ConditionalOfferFactory(name="offer1")
        offer1.set_voucher(voucher)
        result1 = models.BasketDiscount(D("2.00"))

        offer2 = ConditionalOfferFactory(name="offer2")
        offer2.set_voucher(voucher)
        result2 = models.BasketDiscount(D("1.00"))

        self.applications.add(offer1, result1)
        self.applications.add(offer2, result2)

        assert len(self.applications) == 2

        discounts = self.applications.grouped_voucher_discounts
        discounts = [x for x in discounts]
        assert len(discounts) == 1
        assert discounts[0]["voucher"] == voucher
        assert discounts[0]["discount"] == D("3.00")
