from django.test import TestCase

from oscar.apps.offer import models
from oscar.test import factories


class OfferTest(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products range", includes_all_products=True)
        self.basket = factories.create_basket(empty=True)
