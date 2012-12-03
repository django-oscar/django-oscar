from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer import models


class TestAnOfferChangesStatusWhen(TestCase):

    def setUp(self):
        condition, benefit = G(models.Condition), G(models.Benefit)
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=condition, benefit=benefit)

    def test_the_max_discount_is_exceeded(self):
        self.offer.max_discount = D('10.00')
        self.assertTrue(self.offer.is_open)

        # Now bump the total discount and save to see if the status is
        # automatically updated.
        self.offer.total_discount += D('20.00')
        self.offer.save()
        self.assertFalse(self.offer.is_open)

    def test_the_max_global_applications_is_exceeded(self):
        self.offer.max_global_applications = 5
        self.assertTrue(self.offer.is_open)

        self.offer.num_applications += 10
        self.offer.save()
        self.assertFalse(self.offer.is_open)
