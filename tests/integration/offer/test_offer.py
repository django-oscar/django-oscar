from django.test import TestCase

from oscar.apps.offer.views import RangeDetailView
from oscar.test.factories import create_product
from oscar.test.factories.offer import ConditionalOfferFactory


class TestOffer(TestCase):

    def setUp(self):
        self.offer = ConditionalOfferFactory()
        self.non_public_product = create_product(is_public=False)
        self.offer.condition.range.add_product(self.non_public_product)

    def test_non_public_product_not_in_offer(self):      
        self.assertFalse(product in self.offer.products())

    def test_non_public_product_not_in_range_detail_view(self):
        view = RangeDetailView()
        view.range = self.offer.condition.range
        self.assertFalse(product in view.get_queryset())
