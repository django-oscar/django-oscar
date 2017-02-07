from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.offer.results import OfferApplications
from oscar.apps.offer import models


class TestOfferApplicationsWrapper(TestCase):

    def setUp(self):
        offer = models.ConditionalOffer()
        self.applications = OfferApplications()
        for i in range(4):
            self.applications.add(offer, models.BasketDiscount(D('5.00')))

    def test_is_iterable(self):
        for discount in self.applications:
            pass

    def test_aggregates_results_from_same_offer(self):
        self.assertEqual(1, len(list(self.applications)))
