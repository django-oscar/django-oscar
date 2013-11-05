from decimal import Decimal as D

from django.test import TestCase
from django.test.client import RequestFactory
import mock

from oscar.apps.offer import models, utils, custom
from oscar.test import factories
from oscar.test.basket import add_product


class CustomAction(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer):
        condition.consume_items(offer, basket, ())
        return models.PostOrderAction(
            "Something will happen")

    def apply_deferred(self, basket):
        return "Something happened"

    @property
    def description(self):
        return "Will do something"


def create_offer():
    range = models.Range.objects.create(
        name="All products", includes_all_products=True)
    condition = models.CountCondition.objects.create(
        range=range,
        type=models.Condition.COUNT,
        value=1)
    benefit = custom.create_benefit(CustomAction)
    return models.ConditionalOffer.objects.create(
        condition=condition,
        benefit=benefit,
        offer_type=models.ConditionalOffer.SITE)


def apply_offers(basket):
    req = RequestFactory().get('/')
    req.user = mock.Mock()
    utils.Applicator().apply(req, basket)


class TestAnOfferWithAPostOrderAction(TestCase):

    def setUp(self):
        self.basket = factories.create_basket(empty=True)
        add_product(self.basket, D('12.00'), 1)
        create_offer()
        apply_offers(self.basket)

    def test_applies_correctly_to_basket_which_meets_condition(self):
        self.assertEqual(1, len(self.basket.offer_applications))
        self.assertEqual(
            1, len(self.basket.offer_applications.post_order_actions))
        action = self.basket.offer_applications.post_order_actions[0]
        self.assertEqual('Something will happen', action['description'])

    def test_has_discount_recorded_correctly_when_order_is_placed(self):
        order = factories.create_order(basket=self.basket)

        discounts = order.discounts.all()
        self.assertEqual(1, len(discounts))
        self.assertEqual(1, len(order.post_order_actions))

        discount = discounts[0]
        self.assertTrue(discount.is_post_order_action)
        self.assertEqual(D('0.00'), discount.amount)
        self.assertEqual('Something happened', discount.message)
