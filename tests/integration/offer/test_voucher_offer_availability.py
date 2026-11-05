import datetime
from decimal import Decimal as D

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone

from oscar.apps.offer.applicator import Applicator
from oscar.apps.order.utils import OrderCreator
from oscar.core.loading import get_class, get_model
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.utils import place_order

ConditionalOffer = get_model("offer", "ConditionalOffer")
Order = get_model("order", "Order")
SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")


def _discount_for(offer):
    basket = factories.create_basket(empty=True)
    add_product(basket, D("10.00"), 1)
    voucher = factories.VoucherFactory()
    voucher.offers.add(offer)
    basket.vouchers.add(voucher)
    Applicator().apply(basket, AnonymousUser())
    return basket.total_discount


class TestUnavailableVoucherOffer(TestCase):
    def test_open_voucher_offer_discounts_the_basket(self):
        offer = factories.create_offer(
            name="Open voucher offer",
            offer_type=ConditionalOffer.VOUCHER,
        )
        self.assertEqual(_discount_for(offer), D("2.00"))

    def test_suspended_voucher_offer_does_not_discount(self):
        offer = factories.create_offer(
            name="Suspended voucher offer",
            offer_type=ConditionalOffer.VOUCHER,
            status=ConditionalOffer.SUSPENDED,
        )
        self.assertEqual(_discount_for(offer), D("0.00"))

    def test_ended_voucher_offer_does_not_discount(self):
        offer = factories.create_offer(
            name="Ended voucher offer",
            offer_type=ConditionalOffer.VOUCHER,
            end=timezone.now() - datetime.timedelta(days=1),
        )
        self.assertEqual(_discount_for(offer), D("0.00"))

    def test_future_voucher_offer_does_not_discount(self):
        offer = factories.create_offer(
            name="Future voucher offer",
            offer_type=ConditionalOffer.VOUCHER,
            start=timezone.now() + datetime.timedelta(days=1),
        )
        self.assertEqual(_discount_for(offer), D("0.00"))

    def test_place_order_rejects_a_suspended_voucher_offer(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 1)
        offer = factories.create_offer(
            name="Suspended at checkout",
            offer_type=ConditionalOffer.VOUCHER,
        )
        voucher = factories.VoucherFactory()
        voucher.offers.add(offer)
        basket.vouchers.add(voucher)
        Applicator().apply(basket, AnonymousUser())
        self.assertEqual(basket.total_discount, D("2.00"))

        offer.suspend()
        surcharges = SurchargeApplicator().get_applicable_surcharges(basket)
        with self.assertRaises(ValueError):
            place_order(
                OrderCreator(),
                surcharges=surcharges,
                basket=basket,
                order_number="4646",
                user=AnonymousUser(),
            )
        self.assertFalse(Order.objects.filter(number="4646").exists())
