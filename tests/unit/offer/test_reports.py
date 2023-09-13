from django.test import TestCase

from oscar.apps.offer.reports import OfferReportGenerator
from oscar.test.factories import (
    ConditionalOfferFactory,
    OrderDiscountFactory,
    create_order,
)


class OfferReportGeneratorTestCase(TestCase):
    def test_generator_queryset_and_annotation(self):
        offer = ConditionalOfferFactory(pk=2)
        OrderDiscountFactory(
            offer_id=offer.pk, offer_name=offer.name, amount=2, order=create_order()
        )
        OrderDiscountFactory(
            offer_id=offer.pk, offer_name=offer.name, amount=3, order=create_order()
        )
        # Discount on a deleted offer
        OrderDiscountFactory(
            offer_id=1, offer_name="Deleted offer", amount=4, order=create_order()
        )
        queryset = OfferReportGenerator().generate()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0]["offer_id"], 2)
        self.assertEqual(queryset[0]["display_offer_name"], offer.name)
        self.assertEqual(queryset[0]["total_discount"], 5)
        self.assertEqual(queryset[0]["offer"], offer.pk)
        self.assertEqual(queryset[1]["offer_id"], 1)
        self.assertEqual(queryset[1]["display_offer_name"], "Deleted offer")
        self.assertEqual(queryset[1]["total_discount"], 4)
        self.assertEqual(queryset[1]["offer"], None)
