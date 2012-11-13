from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.offer.utils import Applicator
from oscar.apps.offer import models
from oscar.apps.basket.models import Basket
from oscar.test.helpers import create_product


class TestOfferApplicator(TestCase):

    def setUp(self):
        self.applicator = Applicator()
        self.basket = Basket.objects.create()
        self.product = create_product(price=D('100'))
        rng = G(models.Range, includes_all_products=True)
        self.condition = G(models.Condition, range=rng, type="Value",
                           value=D('100'))
        self.benefit = G(models.Benefit, range=rng, type="Absolute",
                         value=D('10'))

    def test_applies_offer_multiple_times_by_default(self):
        self.basket.add_product(self.product, 5)
        offer = models.ConditionalOffer(
            id="test", condition=self.condition, benefit=self.benefit)
        discounts = self.applicator.get_basket_discounts(
            self.basket, [offer])
        self.assertEqual(5, discounts["test"]['freq'])

    def test_respects_maximum_applications_field(self):
        self.basket.add_product(self.product, 5)
        offer = models.ConditionalOffer(
            id="test", condition=self.condition, benefit=self.benefit,
            max_applications=1)
        discounts = self.applicator.get_basket_discounts(
            self.basket, [offer])
        self.assertEqual(1, discounts["test"]['freq'])
