import datetime

from django.test import TestCase
from django.utils import timezone

from oscar.test import factories
from oscar.apps.offer import models


class TestActiveOfferManager(TestCase):

    def test_includes_offers_in_date_range(self):
        # Create offer that is available but with the wrong status
        now = timezone.now()
        start = now - datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=1)
        factories.create_offer(start=start, end=end)

        filtered_offers = models.ConditionalOffer.active.all()
        self.assertEqual(1, len(filtered_offers))

    def test_filters_out_expired_offers(self):
        # Create offer that is available but with the wrong status
        now = timezone.now()
        start = now - datetime.timedelta(days=3)
        end = now - datetime.timedelta(days=1)
        factories.create_offer(start=start, end=end)

        filtered_offers = models.ConditionalOffer.active.all()
        self.assertEqual(0, len(filtered_offers))

    def test_filters_out_offers_yet_to_start(self):
        # Create offer that is available but with the wrong status
        now = timezone.now()
        start = now + datetime.timedelta(days=1)
        end = now + datetime.timedelta(days=3)
        factories.create_offer(start=start, end=end)

        filtered_offers = models.ConditionalOffer.active.all()
        self.assertEqual(0, len(filtered_offers))

    def test_filters_out_suspended_offers(self):
        # Create offer that is available but with the wrong status
        factories.create_offer(
            status=models.ConditionalOffer.SUSPENDED)
        filtered_offers = models.ConditionalOffer.active.all()
        self.assertEqual(0, len(filtered_offers))
