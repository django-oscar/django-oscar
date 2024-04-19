from decimal import Decimal as D
from unittest.mock import Mock

from django.test import TestCase

from oscar.apps.offer import models
from oscar.apps.offer.results import OfferApplications
from oscar.apps.offer.utils import Applicator
from oscar.test.basket import add_product
from oscar.test.factories import (
    BasketFactory,
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    RangeFactory,
)


class TestOfferApplicator(TestCase):
    def setUp(self):
        self.applicator = Applicator()
        self.basket = BasketFactory()
        rng = RangeFactory(includes_all_products=True)
        self.condition = ConditionFactory(
            range=rng,
            type=ConditionFactory._meta.model.VALUE,
            value=D("100"),
            proxy_class=None,
        )
        self.benefit = BenefitFactory(
            range=rng, type=BenefitFactory._meta.model.FIXED, value=D("10")
        )

    def test_applies_offer_multiple_times_by_default(self):
        add_product(self.basket, D("100"), 5)
        offer = ConditionalOfferFactory(
            pk=1, condition=self.condition, benefit=self.benefit
        )
        self.applicator.apply_offers(self.basket, [offer])
        line = self.basket.all_lines()[0]
        self.assertTrue(line.quantity_with_offer_discount(offer) == 5)

    def test_respects_maximum_applications_field(self):
        add_product(self.basket, D("100"), 5)
        offer = ConditionalOfferFactory(
            pk=1,
            condition=self.condition,
            benefit=self.benefit,
            max_basket_applications=1,
        )
        self.applicator.apply_offers(self.basket, [offer])
        line = self.basket.all_lines()[0]
        self.assertTrue(line.quantity_with_offer_discount(offer) == 5)
        applications = self.basket.offer_applications.applications
        self.assertTrue(applications[1]["freq"] == 1)

    def test_uses_offers_in_order_of_descending_priority(self):
        self.applicator.get_site_offers = Mock(
            return_value=[
                models.ConditionalOffer(
                    name="offer1",
                    condition=self.condition,
                    benefit=self.benefit,
                    priority=1,
                )
            ]
        )

        self.applicator.get_user_offers = Mock(
            return_value=[
                models.ConditionalOffer(
                    name="offer2",
                    condition=self.condition,
                    benefit=self.benefit,
                    priority=-1,
                )
            ]
        )

        offers = self.applicator.get_offers(self.basket)
        priorities = [offer.priority for offer in offers]
        self.assertEqual(sorted(priorities, reverse=True), priorities)

    def test_get_site_offers(self):
        models.ConditionalOffer.objects.create(
            name="globaloffer",
            condition=self.condition,
            benefit=self.benefit,
            offer_type=models.ConditionalOffer.SITE,
        )
        models.ConditionalOffer.objects.create(
            name="sessionoffer",
            condition=self.condition,
            benefit=self.benefit,
            offer_type=models.ConditionalOffer.SESSION,
        )

        site_offers = Applicator().get_site_offers()
        # Only one offer should be returned
        self.assertEqual(len(site_offers), 1)
        self.assertEqual(site_offers[0].name, "globaloffer")


class TestOfferApplicationsWrapper(TestCase):
    def setUp(self):
        offer = models.ConditionalOffer()
        self.applications = OfferApplications()
        for _ in range(4):
            self.applications.add(offer, models.BasketDiscount(D("5.00")))

    def test_is_iterable(self):
        for _ in self.applications:
            pass

    def test_aggregates_results_from_same_offer(self):
        self.assertEqual(1, len(list(self.applications)))
