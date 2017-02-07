from decimal import Decimal as D

from django.test import TestCase
from mock import Mock

from oscar.apps.offer import models
from oscar.apps.offer.results import OfferApplications
from oscar.apps.offer.utils import Applicator
from oscar.test.factories import (
    BasketFactory, RangeFactory, BenefitFactory, ConditionFactory,
    ConditionalOfferFactory)

from oscar.test.basket import add_product


class TestOfferApplicator(TestCase):

    def setUp(self):
        self.applicator = Applicator()
        self.basket = BasketFactory()
        rng = RangeFactory(includes_all_products=True)
        self.condition = ConditionFactory(
            range=rng, type=ConditionFactory._meta.model.VALUE,
            value=D('100'), proxy_class=None)
        self.benefit = BenefitFactory(
            range=rng, type=BenefitFactory._meta.model.FIXED,
            value=D('10'), max_affected_items=1)

    def test_applies_offer_multiple_times_by_default(self):
        add_product(self.basket, D('100'), 5)
        offer = ConditionalOfferFactory(
            pk=1, condition=self.condition, benefit=self.benefit)
        self.applicator.apply_offers(self.basket, [offer])
        applications = self.basket.offer_applications.applications
        self.assertEqual(5, applications[1]['freq'])

    def test_respects_maximum_applications_field(self):
        add_product(self.basket, D('100'), 5)
        offer = ConditionalOfferFactory(
            pk=1, condition=self.condition, benefit=self.benefit,
            max_basket_applications=1)
        self.applicator.apply_offers(self.basket, [offer])
        applications = self.basket.offer_applications.applications
        self.assertEqual(1, applications[1]['freq'])

    def test_uses_offers_in_order_of_descending_priority(self):
        self.applicator.get_site_offers = Mock(
            return_value=[models.ConditionalOffer(
                name="offer1", condition=self.condition, benefit=self.benefit,
                priority=1)])

        self.applicator.get_user_offers = Mock(
            return_value=[models.ConditionalOffer(
                name="offer2", condition=self.condition, benefit=self.benefit,
                priority=-1)])

        offers = self.applicator.get_offers(self.basket)
        priorities = [offer.priority for offer in offers]
        self.assertEqual(sorted(priorities, reverse=True), priorities)


class TestOfferApplicationsWrapper(TestCase):

    def setUp(self):
        offer = models.ConditionalOffer()
        self.applications = OfferApplications()
        for i in range(4):
            self.applications.add(offer, models.BasketDiscount(D('5.00')))

    def test_is_iterable(self):
        for discount in self.applications:
            pass

    def test_aggregates_results_from_same_offer(self):
        self.assertEqual(1, len(list(self.applications)))
