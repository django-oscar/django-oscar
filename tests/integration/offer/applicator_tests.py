from decimal import Decimal as D

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
        self.assertEqual(5, self.basket.offer_applications.applications["test"]['freq'])

    def test_respects_maximum_applications_field(self):
        add_product(self.basket, D('100'), 5)
        offer = models.ConditionalOffer(
            id="test", condition=self.condition, benefit=self.benefit,
            max_basket_applications=1)
        self.applicator.apply_offers(self.basket, [offer])
        self.assertEqual(1, self.basket.offer_applications.applications["test"]['freq'])
