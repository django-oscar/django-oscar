from django.test import TestCase

from oscar.apps.offer.views import RangeDetailView
from oscar.test.factories import create_product
from oscar.test.factories.offer import ConditionalOfferFactory


class TestOffer(TestCase):

    def test_non_public_product_not_in_offer(self):
        offer = ConditionalOfferFactory()
        product = create_product(is_public=False)
        offer.condition.range.add_product(product)
        self.assertFalse(product in offer.products())
        view = RangeDetailView()
        view.range = offer.condition.range
        self.assertFalse(product in view.get_queryset())
