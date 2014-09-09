from django.test import TestCase

from oscar.apps.offer import models


class OfferTest(TestCase):
    def setUp(self):
        self.range = models.Range(
            name="All products range", includes_all_products=True)
