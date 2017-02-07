from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer import models, results


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
        result = models.BasketDiscount(D('2.00'))
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.offer_discounts))

    def test_can_filter_post_order_actions(self):
        result = models.PostOrderAction("Something will happen")
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.post_order_actions))
