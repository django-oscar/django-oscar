from django.urls import reverse

from oscar.core.loading import get_model
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

Order = get_model("order", "Order")
UserAddress = get_model("address", "UserAddress")


class LoginRequiredMixin:
    view_name = None
    view_url = None

    def test_requires_login(self):
        response = self.get(self.view_url or reverse(self.view_name), user=None)
        expected_url = "{login_url}?next={forward}".format(
            login_url=reverse("customer:login"),
            forward=self.view_url or reverse(self.view_name),
        )
        self.assertRedirects(response, expected_url)


class TestIndexView(
    LoginRequiredMixin, IndexViewPreConditionsMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:index"

    def test_redirects_customers_to_shipping_address_view(self):
        self.add_product_to_basket()
        response = self.get(reverse("checkout:index"))
        self.assertRedirectsTo(response, "checkout:shipping-address")


class TestShippingAddressView(
    LoginRequiredMixin, ShippingAddressViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:shipping-address"
    next_view_name = "checkout:shipping-method"

    def setUp(self):
        super().setUp()
        self.user_address = factories.UserAddressFactory(
            user=self.user, country=self.create_shipping_country()
        )

    def test_only_shipping_addresses_are_shown(self):
        not_shipping_country = factories.CountryFactory(
            iso_3166_1_a2="US", name="UNITED STATES", is_shipping_country=False
        )
        not_shipping_address = factories.UserAddressFactory(
            user=self.user, country=not_shipping_country, line4="New York"
        )
        self.add_product_to_basket()
        page = self.get(reverse("checkout:shipping-address"))
        page.mustcontain(
            self.user_address.line4,
            self.user_address.country.name,
            no=[not_shipping_address.country.name, not_shipping_address.line4],
        )

    def test_can_select_an_existing_shipping_address(self):
        self.add_product_to_basket()
        page = self.get(reverse("checkout:shipping-address"), user=self.user)
        self.assertIsOk(page)
        form = page.forms["select_shipping_address_%s" % self.user_address.id]
        response = form.submit()
        self.assertRedirectsTo(response, "checkout:shipping-method")


class TestUserAddressUpdateView(LoginRequiredMixin, CheckoutMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        user_address = factories.UserAddressFactory(
            user=self.user, country=self.create_shipping_country()
        )
        self.view_url = reverse(
            "checkout:user-address-update", kwargs={"pk": user_address.pk}
        )

    def test_submitting_valid_form_modifies_user_address(self):
        page = self.get(self.view_url, user=self.user)
        form = page.forms["update_user_address"]
        form["first_name"] = "Tom"
        response = form.submit()
        self.assertRedirectsTo(response, "checkout:shipping-address")
        self.assertEqual("Tom", UserAddress.objects.get().first_name)


class TestUserAddressDeleteView(LoginRequiredMixin, CheckoutMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        self.user_address = factories.UserAddressFactory(
            user=self.user, country=self.create_shipping_country()
        )
        self.view_url = reverse(
            "checkout:user-address-delete", kwargs={"pk": self.user_address.pk}
        )

    def test_can_delete_a_user_address_from_shipping_address_page(self):
        self.add_product_to_basket()
        page = self.get(reverse("checkout:shipping-address"), user=self.user)
        delete_confirm = page.click(href=self.view_url)
        form = delete_confirm.forms["delete_address_%s" % self.user_address.id]
        form.submit()

        # Ensure address is deleted
        user_addresses = UserAddress.objects.filter(user=self.user)
        self.assertEqual(0, len(user_addresses))


class TestShippingMethodView(
    LoginRequiredMixin, ShippingMethodViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:shipping-method"
    next_view_name = "checkout:payment-method"


class TestPaymentMethodView(
    LoginRequiredMixin, PaymentMethodViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:payment-method"


class TestPaymentDetailsView(
    LoginRequiredMixin, PaymentDetailsViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:payment-details"


class TestPaymentDetailsPreviewView(
    LoginRequiredMixin, PaymentDetailsPreviewViewMixin, CheckoutMixin, WebTestCase
):
    view_name = "checkout:preview"


class TestThankYouView(CheckoutMixin, WebTestCase):
    def tests_gets_a_302_when_there_is_no_order(self):
        response = self.get(reverse("checkout:thank-you"), user=self.user, status="*")
        self.assertIsRedirect(response)
        self.assertRedirectsTo(response, "catalogue:index")

    def tests_gets_a_302_when_the_order_id_in_the_session_is_for_a_non_existent_order(
        self,
    ):
        session = self.client.session
        # Put the order ID in the session, mimicking an order that no longer
        # exists, so that we can be redirected to the home page.
        session["checkout_order_id"] = 0
        session.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse("checkout:thank-you"))
        self.assertRedirects(response, reverse("catalogue:index"))

    def tests_custumers_can_reach_the_thank_you_page(self):
        self.add_product_to_basket()
        self.enter_shipping_address()
        thank_you = self.place_order()
        self.assertIsOk(thank_you)

    def test_superusers_can_force_an_order(self):
        self.add_product_to_basket()
        self.enter_shipping_address()
        self.place_order()
        user = self.create_user("admin", "admin@admin.com")
        user.is_superuser = True
        user.save()
        order = Order.objects.get()

        test_url = "%s?order_number=%s" % (reverse("checkout:thank-you"), order.number)
        response = self.get(test_url, status="*", user=user)
        self.assertIsOk(response)

        test_url = "%s?order_id=%s" % (reverse("checkout:thank-you"), order.pk)
        response = self.get(test_url, status="*", user=user)
        self.assertIsOk(response)

    def test_superusers_cannot_force_a_non_existent_order(self):
        user = self.create_user("admin", "admin@admin.com")
        user.is_superuser = True
        user.save()

        test_url = "%s?order_number=%s" % (
            reverse("checkout:thank-you"),
            "non-existent",
        )
        response = self.get(test_url, status="*", user=user)
        self.assertIsRedirect(response)
        self.assertRedirectsTo(response, "catalogue:index")

        test_url = "%s?order_id=%s" % (reverse("checkout:thank-you"), 0)
        response = self.get(test_url, status="*", user=user)
        self.assertIsRedirect(response)
        self.assertRedirectsTo(response, "catalogue:index")

    def test_users_cannot_force_an_other_customer_order(self):
        self.add_product_to_basket()
        self.enter_shipping_address()
        self.place_order()
        user = self.create_user("John", "john@test.com")
        user.save()
        order = Order.objects.get()

        test_url = "%s?order_number=%s" % (reverse("checkout:thank-you"), order.number)
        response = self.get(test_url, status="*", user=user)
        self.assertIsRedirect(response)
        self.assertRedirectsTo(response, "catalogue:index")

        test_url = "%s?order_id=%s" % (reverse("checkout:thank-you"), order.pk)
        response = self.get(test_url, status="*", user=user)
        self.assertIsRedirect(response)
        self.assertRedirectsTo(response, "catalogue:index")
