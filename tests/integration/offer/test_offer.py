from django.test import TestCase

from oscar.test.factories import create_product
from oscar.test.factories.offer import ConditionalOfferFactory


class TestOffer(TestCase):

    def test_non_public_product_not_in_offer(self):
        offer = ConditionalOfferFactory()
        product = create_product(is_public=False)
        offer.condition.range.add_product(product)
        self.assertFalse(product in offer.products())
        self.assertFalse(
            product in offer.condition.range.all_products().browsable())
