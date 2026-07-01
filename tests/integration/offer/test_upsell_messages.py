from decimal import Decimal as D

from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from oscar.apps.basket.views import BasketView
from oscar.apps.offer.applicator import Applicator
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.testcases import WebTestCase

Selector = get_class("partner.strategy", "Selector")


class TestUpsellMessages(WebTestCase):
    def setUp(self):
        super().setUp()

        self.basket = factories.create_basket(empty=True)

        # Create range and add one product to it.
        rng = factories.RangeFactory(name="All products", includes_all_products=True)
        self.product = factories.ProductFactory()
        rng.add_product(self.product)

        # Create offer #1.
        condition1 = factories.ConditionFactory(
            range=rng,
            type=factories.ConditionFactory._meta.model.COUNT,
            value=D("2"),
        )
        benefit1 = factories.BenefitFactory(
            range=rng,
            type=factories.BenefitFactory._meta.model.MULTIBUY,
            value=None,
        )
        self.offer1 = factories.ConditionalOfferFactory(
            condition=condition1,
            benefit=benefit1,
            slug="offer-1",
            start_datetime=now(),
            name="Test offer #1",
            priority=1,
        )

        # Create offer #2.
        condition2 = factories.ConditionFactory(
            range=rng,
            type=factories.ConditionFactory._meta.model.VALUE,
            value=D("1.99"),
        )
        benefit2 = factories.BenefitFactory(
            range=rng,
            type=factories.BenefitFactory._meta.model.MULTIBUY,
            value=None,
        )
        self.offer2 = factories.ConditionalOfferFactory(
            condition=condition2,
            benefit=benefit2,
            slug="offer-2",
            start_datetime=now(),
            name="Test offer #2",
        )

        # Create offer #3.
        condition3 = factories.ConditionFactory(
            range=rng,
            type=factories.ConditionFactory._meta.model.COVERAGE,
            value=1,
        )
        benefit3 = factories.BenefitFactory(
            range=rng,
            type=factories.BenefitFactory._meta.model.MULTIBUY,
            value=None,
        )
        self.offer3 = factories.ConditionalOfferFactory(
            condition=condition3,
            benefit=benefit3,
            slug="offer-3",
            start_datetime=now(),
            name="Test offer #3",
        )

        # Prepare `BasketView` to use `get_upsell_messages` method in tests.
        self.view = BasketView()
        self.view.request = RequestFactory().get(reverse("basket:summary"))
        self.view.request.user = factories.UserFactory()
        self.view.args = []
        self.view.kwargs = {}

    def add_product(self):
        self.basket.add_product(self.product)
        self.basket.strategy = Selector().strategy()
        Applicator().apply(self.basket)

        self.assertBasketUpsellMessagesAreNotNone()

    def assertBasketUpsellMessagesAreNotNone(self):
        messages = self.view.get_upsell_messages(self.basket)
        for message_data in messages:
            # E.g. message data:
            # {
            #     'message': 'Buy 1 more product from All products',
            #     'offer': <ConditionalOffer: Test offer #1>
            # }.
            self.assertIsNotNone(message_data["message"])
            self.assertIsNotNone(message_data["offer"])

    def assertOffersApplied(self, offers):
        applied_offers = self.basket.applied_offers()
        self.assertEqual(len(offers), len(applied_offers))
        for offer in offers:
            self.assertIn(offer.id, applied_offers, msg=offer)

    def test_upsell_messages(self):
        # The basket is empty. No offers are applied.
        self.assertEqual(
            self.offer1.get_upsell_message(self.basket),
            "Buy 2 more products from All products",
        )
        self.assertEqual(
            self.offer2.get_upsell_message(self.basket),
            "Spend £1.99 more from All products",
        )
        self.assertEqual(
            self.offer3.get_upsell_message(self.basket),
            "Buy 1 more product from All products",
        )

        self.add_product()

        # 1 product in the basket. Offer #2 is applied.
        self.assertOffersApplied([self.offer2])
        self.assertEqual(
            self.offer1.get_upsell_message(self.basket),
            "Buy 1 more product from All products",
        )
        self.assertIsNone(self.offer2.get_upsell_message(self.basket))
        self.assertEqual(
            self.offer3.get_upsell_message(self.basket),
            "Buy 1 more product from All products",
        )

        self.add_product()

        # 2 products in the basket. Offers #1 is applied.
        self.assertOffersApplied([self.offer1])
        self.assertIsNone(self.offer1.get_upsell_message(self.basket))
        self.assertEqual(
            self.offer2.get_upsell_message(self.basket),
            "Spend £1.99 more from All products",
        )
        self.assertEqual(
            self.offer3.get_upsell_message(self.basket),
            "Buy 1 more product from All products",
        )

        self.add_product()

        # 3 products in the basket. Offers #1 and #2 are applied.
        self.assertOffersApplied([self.offer1, self.offer2])
        self.assertIsNone(self.offer1.get_upsell_message(self.basket))
        self.assertIsNone(self.offer2.get_upsell_message(self.basket))
        self.assertEqual(
            self.offer3.get_upsell_message(self.basket),
            "Buy 1 more product from All products",
        )

        self.add_product()

        # 4 products in the basket. All offers are applied.
        self.assertOffersApplied([self.offer1, self.offer2, self.offer3])
        self.assertIsNone(self.offer1.get_upsell_message(self.basket))
        self.assertIsNone(self.offer2.get_upsell_message(self.basket))
        self.assertIsNone(self.offer3.get_upsell_message(self.basket))
