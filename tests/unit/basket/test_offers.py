from decimal import ROUND_HALF_UP
from decimal import Decimal as D

from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse

from oscar.core.loading import get_class, get_classes, get_model
from oscar.test.factories import UserFactory

Basket = get_model("basket", "Basket")
Product = get_model("catalogue", "Product")
factory = RequestFactory()
Applicator = get_class("offer.applicator", "Applicator")
Selector, UK = get_classes("partner.strategy", ["Selector", "UK"])


class UKSelector(Selector):
    # pylint: disable=unused-argument
    def strategy(self, request=None, user=None, **kwargs):
        return UK(request)


def money(amount):
    return amount.quantize(D("0.01"), ROUND_HALF_UP)


def get_user_basket(user, request):
    editable_baskets = Basket.objects.filter(status__in=["Open", "Saved"])
    basket, __ = editable_baskets.get_or_create(owner=user)
    basket.strategy = UKSelector().strategy(request=request, user=user)
    basket.reset_offer_applications()
    if not basket.is_empty:
        Applicator().apply(basket, user, request)
    request.session[settings.OSCAR_BASKET_COOKIE_OPEN] = basket.pk
    request.session.save()
    return basket


class OfferTest(TestCase):
    fixtures = ["catalogue", "offer"]

    def check_general_truths(self, basket):
        inverse_tax_multiplier = D(1) / (D(1) + UK.rate)
        calculated_total_excl_tax = money(
            inverse_tax_multiplier * basket.total_incl_tax
        )

        self.assertEqual(
            calculated_total_excl_tax,
            basket.total_excl_tax,
            "The total price without tax should conform to the standard "
            "formula for calculating tax (as a percentage)",
        )
        self.assertAlmostEqual(
            basket.total_excl_tax_excl_discounts / basket.total_incl_tax_excl_discounts,
            basket.total_excl_tax / basket.total_incl_tax,
            4,
            "The ratio of price with tax and without tax should be the same for the "
            "price with and without discounts. If that is not the case people would "
            "be able to change the tax they must pay by gaming the discount.",
        )
        self.assertNotAlmostEqual(
            basket.total_excl_tax_excl_discounts - basket.total_excl_tax,
            basket.total_incl_tax_excl_discounts - basket.total_incl_tax,
            2,
            "The discount over the total excluding tax can never be the same as "
            "the discount over the total including tax. Otherwise our tax rate"
            "would not be linear over the amount.",
        )
        self.assertEqual(
            basket.total_excl_tax + basket.total_tax,
            basket.total_incl_tax,
            "The tax summation should amount to the total_incl_tax",
        )

    def test_offer_incl_tax(self):
        "The offer should be calculated as if it was declared including tax"
        with self.settings(OSCAR_OFFERS_INCL_TAX=True):
            self.assertEqual(Basket.objects.count(), 0)

            admin = UserFactory()
            self.client.force_login(admin)

            # throw an item in the basket
            basket_add_url = reverse("basket:add", args=(2,))
            body = {"quantity": 1}
            response = self.client.post(basket_add_url, body)

            # throw another item in the basket so the offer activates
            basket_add_url = reverse("basket:add", args=(3,))
            body = {"quantity": 2}
            response = self.client.post(basket_add_url, body)

            request = factory.post(basket_add_url, body)
            request.user = admin
            request.session = self.client.session

            basket = get_user_basket(admin, request)

            self.assertEqual(response.status_code, 302)
            self.assertEqual(Basket.objects.count(), 1)

            # now go and check if the offer was applied correctly
            self.assertEqual(
                basket.total_incl_tax_excl_discounts - basket.total_incl_tax,
                D("10.00"),
                "The offer should be a flat 10 pound discount on the total "
                "including tax",
            )
            self.assertEqual(
                basket.total_discount,
                D("10.00"),
                "The total discount property should properly reflect the discount"
                "applied.",
            )
            self.check_general_truths(basket)

    def test_offer_excl_tax(self):
        "The offer should be calculated as if it was declared excluding tax"
        with self.settings(OSCAR_OFFERS_INCL_TAX=False):
            self.assertEqual(Basket.objects.count(), 0)

            admin = UserFactory()
            self.client.force_login(admin)

            # throw an item in the basket
            basket_add_url = reverse("basket:add", args=(2,))
            body = {"quantity": 1}
            response = self.client.post(basket_add_url, body)

            # throw another item in the basket so the offer activates
            basket_add_url = reverse("basket:add", args=(3,))
            body = {"quantity": 2}
            response = self.client.post(basket_add_url, body)

            # now go and check if dat offer was handled correctly
            request = factory.post(basket_add_url, body)
            request.user = admin
            request.session = self.client.session

            basket = get_user_basket(admin, request)

            self.assertEqual(response.status_code, 302)
            self.assertEqual(Basket.objects.count(), 1)

            # now go and check if the offer was applied correctly
            self.assertEqual(
                basket.total_excl_tax_excl_discounts - basket.total_excl_tax,
                D("10.00"),
                "The offer should be a flat 10 pound discount on the total "
                "excluding tax",
            )
            self.assertEqual(
                basket.total_discount,
                D("10.00"),
                "The total discount property should properly reflect the discount"
                "applied.",
            )

            self.check_general_truths(basket)
