import datetime

from django.test import TestCase

from oscar.apps.offer import models


class TestAConditionalOffer(TestCase):

    def test_is_active(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 01, 10)
        end = datetime.date(2011, 02, 01)
        offer = models.ConditionalOffer(start_date=start, end_date=end)
        self.assertTrue(offer.is_active(test))

    def test_is_inactive(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 03, 10)
        end = datetime.date(2011, 02, 01)
        offer = models.ConditionalOffer(start_date=start, end_date=end)
        self.assertFalse(offer.is_active(test))
