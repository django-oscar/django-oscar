from decimal import Decimal as D

from mock import Mock

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer.utils import Applicator
from oscar.apps.offer import models
from oscar.test.basket import add_product
from oscar.test import factories


class TestOfferApplicator(TestCase):

    def setUp(self):
        self.applicator = Applicator()
        self.basket = factories.create_basket(empty=True)
        rng = G(models.Range, includes_all_products=True)
        self.condition = G(models.Condition, range=rng, type="Value",
                           value=D('100'), proxy_class=None)
        self.benefit = G(models.Benefit, range=rng, type="Absolute",
                         value=D('10'))

    def test_applies_offer_multiple_times_by_default(self):
        add_product(self.basket, D('100'), 5)
        offer = models.ConditionalOffer(
            id="test", condition=self.condition, benefit=self.benefit)
        self.applicator.apply_offers(self.basket, [offer])
        applications = self.basket.offer_applications.applications
        self.assertEqual(5, applications["test"]['freq'])

    def test_respects_maximum_applications_field(self):
        add_product(self.basket, D('100'), 5)
        offer = models.ConditionalOffer(
            id="test", condition=self.condition, benefit=self.benefit,
            max_basket_applications=1)
        self.applicator.apply_offers(self.basket, [offer])
        applications = self.basket.offer_applications.applications
        self.assertEqual(1, applications["test"]['freq'])

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
