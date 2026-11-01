import hashlib
import hmac
import json
import time
from decimal import Decimal
from unittest import mock

import stripe
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from oscar.core.loading import get_model
from oscar.test.factories import (
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    CountryFactory,
    RangeFactory,
    VoucherFactory,
    create_product,
)
from rest_framework.authtoken.models import Token

from apps.stripe_checkout.models import StripeCheckout, StripeCustomer

User = get_user_model()
Basket = get_model("basket", "Basket")
Order = get_model("order", "Order")

WEBHOOK_SECRET = "whsec_test"
SESSION = "apps.stripe_checkout.services.stripe.checkout.Session"
CUSTOMER = "apps.stripe_checkout.services.stripe.Customer"
PAYMENT_METHOD = "apps.stripe_checkout.services.stripe.PaymentMethod"


def stripe_session(
    session_id="cs_test_1", status="open", payment_status="unpaid", amount_total=3400
):
    return {
        "id": session_id,
        "object": "checkout.session",
        "url": "https://checkout.stripe.com/c/pay/" + session_id,
        "status": status,
        "payment_status": payment_status,
        "amount_total": amount_total,
        "payment_intent": "pi_test_1" if payment_status == "paid" else None,
    }


def paid_session(**kwargs):
    return stripe_session(status="complete", payment_status="paid", **kwargs)


@override_settings(
    STRIPE_SECRET_KEY="sk_test_123",
    STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET,
    KHAFA_SHIPPING_CHARGE="10.00",
)
class StripeCheckoutTest(TestCase):
    def setUp(self):
        CountryFactory(iso_3166_1_a2="FR", printable_name="France")
        self.shirt = create_product(
            title="Linen Shirt", price=Decimal("12.00"), num_in_stock=3
        )
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.auth = {
            "HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"
        }
        patcher = mock.patch(CUSTOMER + ".create", return_value={"id": "cus_test_1"})
        self.customer_create = patcher.start()
        self.addCleanup(patcher.stop)
        self.address = {
            "first_name": "Jane",
            "last_name": "Doe",
            "line1": "1 rue de la Paix",
            "line4": "Paris",
            "postcode": "75002",
            "country": "http://testserver" + reverse("country-detail", args=["FR"]),
            "phone_number": "+33612345678",
        }

    # helpers

    def add(self, product=None, quantity=2, **auth):
        return self.client.post(
            reverse("api-cart-lines"),
            {"product": (product or self.shirt).pk, "quantity": quantity},
            content_type="application/json",
            **auth,
        )

    def start(self, session=None, **data):
        body = {"shipping_address": self.address, **data}
        auth = body.pop("auth", {})
        with mock.patch(
            SESSION + ".create", return_value=session or stripe_session()
        ) as create:
            response = self.client.post(
                reverse("api-checkout"), body, content_type="application/json", **auth
            )
        return response, create

    def webhook(self, event_type, session, secret=WEBHOOK_SECRET):
        payload = json.dumps(
            {
                "id": "evt_1",
                "object": "event",
                "type": event_type,
                "data": {"object": session},
            }
        )
        timestamp = int(time.time())
        signature = hmac.new(
            secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256
        ).hexdigest()
        return self.client.post(
            reverse("api-checkout-stripe-webhook"),
            payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
        )

    def status(self, session_id="cs_test_1", stripe_state=None, **auth):
        with mock.patch(
            SESSION + ".retrieve", return_value=stripe_state or stripe_session()
        ):
            return self.client.get(
                reverse("api-checkout-status", args=[session_id]), **auth
            )

    # summary

    def test_summary_includes_the_flat_delivery(self):
        self.add()
        data = self.client.get(reverse("api-checkout")).json()
        self.assertEqual(data["basket_total"], "24.00")
        self.assertEqual(data["shipping_method"]["code"], "flat-rate")
        self.assertEqual(data["shipping_method"]["charge"], "10.00")
        self.assertEqual(data["order_total"], "34.00")
        self.assertTrue(data["guest_email_required"])
        self.assertTrue(data["payment_available"])

    @override_settings(KHAFA_SHIPPING_CHARGE="4.50")
    def test_delivery_charge_comes_from_the_settings(self):
        self.add(**self.auth)
        data = self.client.get(reverse("api-checkout"), **self.auth).json()
        self.assertEqual(data["shipping_method"]["charge"], "4.50")
        self.assertFalse(data["guest_email_required"])

    # start

    def test_guest_starts_a_payment_and_the_basket_is_frozen(self):
        self.add()
        response, create = self.start(guest_email="guest@example.com")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["url"], "https://checkout.stripe.com/c/pay/cs_test_1")
        self.assertEqual(data["status"], "open")
        self.assertEqual(data["amount"], "34.00")

        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["customer_email"], "guest@example.com")
        self.assertEqual(kwargs["api_key"], "sk_test_123")
        self.assertEqual(
            sum(i["price_data"]["unit_amount"] for i in kwargs["line_items"]), 3400
        )
        self.assertEqual(
            kwargs["line_items"][0]["price_data"]["product_data"]["name"],
            "Linen Shirt × 2",
        )
        self.assertTrue(
            kwargs["success_url"].startswith(
                "http://testserver/api/checkout/return/?session_id="
            )
        )
        self.assertIn("{CHECKOUT_SESSION_ID}", kwargs["success_url"])

        checkout = StripeCheckout.objects.get()
        self.assertEqual(checkout.basket.status, Basket.FROZEN)
        self.assertEqual(checkout.shipping_address["country"], "FR")
        self.assertIsNone(checkout.user)
        # the cart is now a new, empty basket
        self.assertEqual(self.client.get(reverse("api-cart")).json()["num_items"], 0)

    def test_web_client_comes_back_to_the_web_app(self):
        self.add()
        __, create = self.start(guest_email="guest@example.com", client="web")
        self.assertEqual(
            create.call_args.kwargs["success_url"],
            "http://testserver/app/?checkout_session={CHECKOUT_SESSION_ID}",
        )

    def test_guest_needs_an_email(self):
        self.add()
        response, create = self.start()
        self.assertEqual(response.status_code, 400)
        self.assertIn("guest_email", response.json())
        create.assert_not_called()

    def test_signed_in_user_pays_as_their_stripe_customer(self):
        self.add(**self.auth)
        response, create = self.start(auth=self.auth)
        self.assertEqual(response.status_code, 201)
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["customer"], "cus_test_1")
        self.assertNotIn("customer_email", kwargs)
        self.assertEqual(
            kwargs["saved_payment_method_options"]["payment_method_save"], "enabled"
        )
        self.customer_create.assert_called_once()
        self.assertEqual(
            self.customer_create.call_args.kwargs["email"], "jdoe@example.com"
        )
        checkout = StripeCheckout.objects.get()
        self.assertEqual(checkout.user, self.user)
        self.assertEqual(checkout.email, "jdoe@example.com")

    def test_stripe_customer_is_created_once(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        # the first basket is frozen, the user fills a new one
        self.add(quantity=1, **self.auth)
        __, create = self.start(
            session=stripe_session(session_id="cs_test_2"), auth=self.auth
        )
        self.assertEqual(create.call_args.kwargs["customer"], "cus_test_1")
        self.customer_create.assert_called_once()
        self.assertEqual(StripeCustomer.objects.get().customer_id, "cus_test_1")

    def test_empty_basket_is_refused(self):
        response, create = self.start(auth=self.auth)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())
        create.assert_not_called()

    def test_invalid_address_is_refused(self):
        self.add(**self.auth)
        self.address.pop("line1")
        response, __ = self.start(auth=self.auth)
        self.assertEqual(response.status_code, 400)
        self.assertIn("line1", response.json()["shipping_address"])

    def test_sold_out_line_is_refused(self):
        self.add(**self.auth)
        stockrecord = self.shirt.stockrecords.get()
        stockrecord.num_in_stock = 1
        stockrecord.save()
        response, create = self.start(auth=self.auth)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Linen Shirt", response.json()["non_field_errors"][0])
        create.assert_not_called()

    @override_settings(STRIPE_SECRET_KEY="")
    def test_payment_unavailable_without_keys(self):
        self.add(**self.auth)
        response, __ = self.start(auth=self.auth)
        self.assertEqual(response.status_code, 503)

    def test_stripe_failure_leaves_the_basket_open(self):
        self.add(**self.auth)
        with mock.patch(
            SESSION + ".create", side_effect=stripe.APIConnectionError("down")
        ):
            response = self.client.post(
                reverse("api-checkout"),
                {"shipping_address": self.address},
                content_type="application/json",
                **self.auth,
            )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            self.client.get(reverse("api-cart"), **self.auth).json()["num_items"], 2
        )

    def test_voucher_discount_is_charged(self):
        everything = RangeFactory(includes_all_products=True)
        offer = ConditionalOfferFactory(
            offer_type="Voucher",
            condition=ConditionFactory(range=everything, type="Count", value=1),
            benefit=BenefitFactory(range=everything, type="Percentage", value=10),
        )
        VoucherFactory(code="WELCOME10").offers.add(offer)
        self.add(**self.auth)
        self.client.post(
            reverse("api-cart-vouchers"), {"code": "WELCOME10"},
            content_type="application/json", **self.auth,
        )  # fmt: skip
        response, create = self.start(
            auth=self.auth, session=stripe_session(amount_total=3160)
        )
        self.assertEqual(response.json()["amount"], "31.60")
        self.assertEqual(
            sum(
                i["price_data"]["unit_amount"]
                for i in create.call_args.kwargs["line_items"]
            ),
            3160,
        )

        self.webhook("checkout.session.completed", paid_session(amount_total=3160))
        order = Order.objects.get()
        self.assertEqual(order.total_incl_tax, Decimal("31.60"))
        self.assertEqual(order.basket_discounts.count(), 1)

    # payment

    def test_webhook_places_the_order_once(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        self.assertEqual(
            self.webhook("checkout.session.completed", paid_session()).status_code, 200
        )
        self.assertEqual(
            self.webhook("checkout.session.completed", paid_session()).status_code, 200
        )

        order = Order.objects.get()
        checkout = StripeCheckout.objects.get()
        self.assertEqual(checkout.status, "paid")
        self.assertEqual(checkout.order, order)
        self.assertEqual(order.number, checkout.order_number)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_incl_tax, Decimal("34.00"))
        self.assertEqual(order.shipping_incl_tax, Decimal("10.00"))
        self.assertEqual(order.shipping_address.line4, "Paris")
        self.assertEqual(order.status, "Pending")
        source = order.sources.get()
        self.assertEqual(source.source_type.name, "Stripe")
        self.assertEqual(source.amount_debited, Decimal("34.00"))
        self.assertEqual(source.reference, "pi_test_1")
        self.assertEqual(order.payment_events.get().event_type.name, "Paid")
        self.assertEqual(checkout.basket.status, Basket.SUBMITTED)
        self.assertEqual(self.shirt.stockrecords.get().num_allocated, 2)

    def test_order_confirmation_email_is_sent(self):
        self.add()
        self.start(guest_email="guest@example.com")
        with self.captureOnCommitCallbacks(execute=True):
            self.webhook("checkout.session.completed", paid_session())
        order = Order.objects.get()
        self.assertIsNone(order.user)
        self.assertEqual(order.guest_email, "guest@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["guest@example.com"])

    def test_webhook_with_a_bad_signature_is_refused(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        response = self.webhook(
            "checkout.session.completed", paid_session(), secret="whsec_other"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_status_poll_places_the_order_before_the_webhook(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        data = self.status(stripe_state=paid_session(), **self.auth).json()
        self.assertEqual(data["status"], "paid")
        self.assertEqual(
            data["order"]["number"], StripeCheckout.objects.get().order_number
        )
        self.assertEqual(data["order"]["total_incl_tax"], "34.00")
        # the webhook arriving afterwards changes nothing
        self.webhook("checkout.session.completed", paid_session())
        self.assertEqual(Order.objects.count(), 1)

    def test_status_while_waiting(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        data = self.status(**self.auth).json()
        self.assertEqual(data["status"], "open")
        self.assertIsNone(data["order"])

    def test_unknown_session_is_not_found(self):
        self.assertEqual(self.status("cs_unknown").status_code, 404)

    # expiry and cancel

    def test_expired_session_gives_the_basket_back_to_the_guest(self):
        self.add()
        self.start(guest_email="guest@example.com")
        self.webhook("checkout.session.expired", stripe_session(status="expired"))
        checkout = StripeCheckout.objects.get()
        self.assertEqual(checkout.status, "expired")
        self.assertEqual(checkout.basket.status, Basket.OPEN)

        self.assertEqual(
            self.status(stripe_state=stripe_session(status="expired")).json()["status"],
            "expired",
        )
        cart = self.client.get(reverse("api-cart")).json()
        self.assertEqual(cart["id"], checkout.basket.pk)
        self.assertEqual(cart["num_items"], 2)

    def test_cancel_gives_the_basket_back(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        with mock.patch(
            SESSION + ".expire", return_value=stripe_session(status="expired")
        ) as expire:
            data = self.client.post(
                reverse("api-checkout-cancel", args=["cs_test_1"]), **self.auth
            ).json()
        expire.assert_called_once()
        self.assertEqual(data["status"], "canceled")
        self.assertEqual(
            self.client.get(reverse("api-cart"), **self.auth).json()["num_items"], 2
        )

    def test_cancel_after_payment_places_the_order(self):
        self.add(**self.auth)
        self.start(auth=self.auth)
        with mock.patch(
            SESSION + ".expire",
            side_effect=stripe.InvalidRequestError("complete", None),
        ), mock.patch(SESSION + ".retrieve", return_value=paid_session()):
            data = self.client.post(
                reverse("api-checkout-cancel", args=["cs_test_1"]), **self.auth
            ).json()
        self.assertEqual(data["status"], "paid")
        self.assertTrue(Order.objects.exists())

    def test_return_page(self):
        self.assertContains(
            self.client.get(reverse("api-checkout-return")), "payment has been received"
        )
        self.assertContains(
            self.client.get(reverse("api-checkout-return"), {"canceled": 1}),
            "Payment canceled",
        )


def stripe_card(pm_id="pm_test_visa", customer="cus_test_1", name="Jane Doe"):
    # a real Stripe object: unlike a dict, it has no .get()
    return stripe.PaymentMethod.construct_from(
        {
            "id": pm_id,
            "object": "payment_method",
            "customer": customer,
            "billing_details": {"name": name},
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 4,
                "exp_year": 2030,
            },
        },
        "sk_test_123",
    )


@override_settings(STRIPE_SECRET_KEY="sk_test_123")
class PaymentMethodsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.user.first_name, self.user.last_name = "Jane", "Doe"
        self.user.save()
        self.auth = {
            "HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"
        }
        patcher = mock.patch(CUSTOMER + ".create", return_value={"id": "cus_test_1"})
        self.customer_create = patcher.start()
        self.addCleanup(patcher.stop)

    def with_customer(self):
        StripeCustomer.objects.create(user=self.user, customer_id="cus_test_1")

    def setup_page(self, **data):
        session = {
            "id": "cs_test_setup_1",
            "url": "https://checkout.stripe.com/c/pay/cs_test_setup_1",
        }
        with mock.patch(SESSION + ".create", return_value=session) as create:
            response = self.client.post(
                reverse("api-payment-methods"),
                data,
                content_type="application/json",
                **self.auth,
            )
        return response, create

    def remove(self, pm_id="pm_test_visa", card=None):
        with mock.patch(
            PAYMENT_METHOD + ".retrieve", return_value=card or stripe_card(pm_id)
        ), mock.patch(PAYMENT_METHOD + ".detach") as detach:
            response = self.client.delete(
                reverse("api-payment-method", args=[pm_id]), **self.auth
            )
        return response, detach

    def test_token_required(self):
        self.assertEqual(
            self.client.get(reverse("api-payment-methods")).status_code, 401
        )

    def test_no_cards_before_the_first_one(self):
        with mock.patch(CUSTOMER + ".list_payment_methods") as list_methods:
            response = self.client.get(reverse("api-payment-methods"), **self.auth)
        self.assertEqual(response.json(), [])
        # no Stripe customer just to list nothing
        list_methods.assert_not_called()
        self.customer_create.assert_not_called()

    def test_lists_the_cards(self):
        self.with_customer()
        cards = {"data": [stripe_card(), stripe_card("pm_test_2", name=None)]}
        with mock.patch(
            CUSTOMER + ".list_payment_methods", return_value=cards
        ) as list_methods:
            response = self.client.get(reverse("api-payment-methods"), **self.auth)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": "pm_test_visa",
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 4,
                    "exp_year": 2030,
                    "name": "Jane Doe",
                },
                {
                    "id": "pm_test_2",
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 4,
                    "exp_year": 2030,
                    "name": "",
                },
            ],
        )
        self.assertEqual(list_methods.call_args.args, ("cus_test_1",))
        self.assertEqual(list_methods.call_args.kwargs["type"], "card")

    def test_stripe_unreachable_while_listing(self):
        self.with_customer()
        with mock.patch(
            CUSTOMER + ".list_payment_methods",
            side_effect=stripe.APIConnectionError("down"),
        ):
            response = self.client.get(reverse("api-payment-methods"), **self.auth)
        self.assertEqual(response.status_code, 502)
        self.assertIn("detail", response.json())

    def test_test_and_live_customers_are_separate(self):
        StripeCustomer.objects.create(
            user=self.user, customer_id="cus_live_1", livemode=True
        )
        with mock.patch(CUSTOMER + ".list_payment_methods") as list_methods:
            self.assertEqual(
                self.client.get(reverse("api-payment-methods"), **self.auth).json(), []
            )
        list_methods.assert_not_called()

    def test_add_a_card_opens_a_setup_page(self):
        response, create = self.setup_page()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "session_id": "cs_test_setup_1",
                "url": "https://checkout.stripe.com/c/pay/cs_test_setup_1",
            },
        )
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["mode"], "setup")
        self.assertEqual(kwargs["customer"], "cus_test_1")
        self.assertEqual(
            kwargs["success_url"],
            "http://testserver/api/payment-methods/return/"
            "?session_id={CHECKOUT_SESSION_ID}",
        )
        self.assertTrue(kwargs["cancel_url"].endswith("&canceled=1"))
        self.assertEqual(
            self.customer_create.call_args.kwargs,
            {
                "api_key": "sk_test_123",
                "email": "jdoe@example.com",
                "name": "Jane Doe",
                "metadata": {"user_id": str(self.user.pk)},
            },
        )
        customer = StripeCustomer.objects.get()
        self.assertEqual(customer.user, self.user)
        self.assertFalse(customer.livemode)

    def test_web_client_comes_back_to_the_web_app(self):
        self.with_customer()
        __, create = self.setup_page(client="web")
        self.assertEqual(
            create.call_args.kwargs["success_url"],
            "http://testserver/app/?payment_method_session={CHECKOUT_SESSION_ID}",
        )
        self.customer_create.assert_not_called()

    def test_add_a_card_without_stripe_key(self):
        with override_settings(STRIPE_SECRET_KEY=""):
            response, create = self.setup_page()
        self.assertEqual(response.status_code, 503)
        create.assert_not_called()

    def test_stripe_failure_when_adding_a_card(self):
        with mock.patch(
            SESSION + ".create", side_effect=stripe.APIConnectionError("down")
        ):
            response = self.client.post(
                reverse("api-payment-methods"), {}, content_type="application/json",
                **self.auth,
            )  # fmt: skip
        self.assertEqual(response.status_code, 502)

    def test_remove_a_card(self):
        self.with_customer()
        response, detach = self.remove()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(detach.call_args.args, ("pm_test_visa",))

    def test_card_of_someone_else_is_not_found(self):
        self.with_customer()
        response, detach = self.remove(card=stripe_card(customer="cus_other"))
        self.assertEqual(response.status_code, 404)
        detach.assert_not_called()

    def test_unknown_card_is_not_found(self):
        self.with_customer()
        with mock.patch(
            PAYMENT_METHOD + ".retrieve",
            side_effect=stripe.InvalidRequestError("No such PaymentMethod", "id"),
        ):
            response = self.client.delete(
                reverse("api-payment-method", args=["pm_nope"]), **self.auth
            )
        self.assertEqual(response.status_code, 404)

    def test_remove_without_customer_is_not_found(self):
        response, detach = self.remove()
        self.assertEqual(response.status_code, 404)
        detach.assert_not_called()

    def test_return_page(self):
        self.assertContains(
            self.client.get(reverse("api-payment-methods-return")), "Card saved"
        )
        self.assertContains(
            self.client.get(reverse("api-payment-methods-return"), {"canceled": 1}),
            "No card added",
        )
