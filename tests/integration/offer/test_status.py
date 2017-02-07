from decimal import Decimal as D

from django.test import TestCase

from oscar.core.loading import get_model
from oscar.test.factories import ConditionalOfferFactory


class TestAnOfferChangesStatusWhen(TestCase):

    def setUp(self):
        ConditionalOffer = get_model('offer', 'ConditionalOffer')
        self.offer = ConditionalOfferFactory(
            offer_type=ConditionalOffer.SITE)

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
