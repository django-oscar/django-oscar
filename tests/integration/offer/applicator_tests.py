from decimal import Decimal as D

from django.test import TestCase
from mock import Mock

from oscar.apps.offer import models
from oscar.apps.offer.utils import Applicator
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.factories import (
    BenefitFactory, ConditionalOfferFactory, ConditionFactory, RangeFactory)


class TestOfferApplicator(TestCase):

    def setUp(self):
        self.applicator = Applicator()
        self.basket = factories.create_basket(empty=True)
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
