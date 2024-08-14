import sys
from importlib import import_module, reload
from unittest import mock
from urllib.parse import quote

from django.conf import settings
from django.test.utils import override_settings
from django.urls import clear_url_caches, reverse

from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.testcases import WebTestCase

from . import (
    CheckoutMixin,
    IndexViewPreConditionsMixin,
    PaymentDetailsPreviewViewMixin,
    PaymentDetailsViewMixin,
    PaymentMethodViewMixin,
    ShippingAddressViewMixin,
    ShippingMethodViewMixin,
)

GatewayForm = get_class("checkout.forms", "GatewayForm")


def reload_url_conf():
    # Reload URLs to pick up the overridden settings
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])
    import_module(settings.ROOT_URLCONF)
    clear_url_caches()


class AnonymousMixin:
    is_anonymous = True

    def setUp(self):
        reload_url_conf()
        super().setUp()

    # Disable skip conditions, so that we do not first get redirected forwards
    # pylint: disable=unused-argument
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    def test_does_not_require_login(
        self,
        mock_skip_unless_payment_is_required,
        mock_skip_unless_basket_requires_shipping,
    ):
        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, "basket:summary")


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestIndexView(
    AnonymousMixin, IndexViewPreConditionsMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:index"

    def test_redirects_new_customers_to_registration_page(self):
        self.add_product_to_basket()
        page = self.get(reverse("checkout:index"))

        form = page.form
        form["options"].select(GatewayForm.NEW)
        new_user_email = "newcustomer@test.com"
        form["username"].value = new_user_email
        response = form.submit()

        expected_url = "{register_url}?next={forward}&email={email}".format(
            register_url=reverse("customer:register"),
            forward=reverse("checkout:shipping-address"),
            email=quote(new_user_email),
        )
        self.assertRedirects(response, expected_url)

    def test_redirects_existing_customers_to_shipping_address_page(self):
        password = "password"
        user = factories.UserFactory(password=password)
        self.add_product_to_basket()
        page = self.get(reverse("checkout:index"))
        form = page.form
        form.select("options", GatewayForm.EXISTING)
        form["username"].value = user.email
        form["password"].value = password
        response = form.submit()
        self.assertRedirectsTo(response, "checkout:shipping-address")

    def test_redirects_guest_customers_to_shipping_address_page(self):
        self.add_product_to_basket()
        page = self.get(reverse("checkout:index"))
        form = page.form
        form.select("options", GatewayForm.GUEST)
        form["username"] = "guest@example.com"
        response = form.submit()
        self.assertRedirectsTo(response, "checkout:shipping-address")

    def test_prefill_form_with_email_for_returning_guest(self):
        self.add_product_to_basket()
        email = "forgetfulguest@test.com"
        self.enter_guest_details(email)
        page = self.get(reverse("checkout:index"))
        self.assertEqual(email, page.form["username"].value)

    def test_auto_select_existing_user(self):
        email = "forgetfulguest@test.com"
        self.create_user(email, email, self.password)

        self.add_product_to_basket()

        # select guest checkout
        page = self.get(reverse("checkout:index"))
        form = page.form
        form["options"].select(GatewayForm.GUEST)
        form["username"].value = email

        response = form.submit()

        # since this user allready exists
        self.assertEqual(email, response.form["username"].value)
        self.assertEqual(
            GatewayForm.EXISTING,
            response.form["options"].value,
            "Since this user has an account, the GatewayForm should "
            "be changed to existing, so the user can enter his password",
        )


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingAddressView(
    AnonymousMixin, ShippingAddressViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:shipping-address"
    next_view_name = "checkout:shipping-method"


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestShippingMethodView(
    AnonymousMixin, ShippingMethodViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:shipping-method"
    next_view_name = "checkout:payment-method"


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentMethodView(
    AnonymousMixin, PaymentMethodViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:payment-method"


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentDetailsView(
    AnonymousMixin, PaymentDetailsViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:payment-details"


@override_settings(OSCAR_ALLOW_ANON_CHECKOUT=True)
class TestPaymentDetailsPreviewView(
    AnonymousMixin, PaymentDetailsPreviewViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:preview"

    def test_placing_order_saves_guest_email_with_order(self):
        preview = self.ready_to_place_an_order()
        thank_you = preview.forms["place_order_form"].submit().follow()
        order = thank_you.context["order"]
        self.assertEqual("hello@egg.com", order.guest_email)
