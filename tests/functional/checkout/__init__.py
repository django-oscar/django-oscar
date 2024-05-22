# pylint: disable=unused-argument, no-value-for-parameter
from decimal import Decimal as D
from http import client as http_client
from unittest import mock

from django.urls import reverse

from oscar.apps.shipping import methods
from oscar.core.loading import get_class, get_classes, get_model
from oscar.test import factories

Basket = get_model("basket", "Basket")
ConditionalOffer = get_model("offer", "ConditionalOffer")
Order = get_model("order", "Order")

FailedPreCondition = get_class("checkout.exceptions", "FailedPreCondition")
GatewayForm = get_class("checkout.forms", "GatewayForm")
UnableToPlaceOrder = get_class("order.exceptions", "UnableToPlaceOrder")
RedirectRequired, UnableToTakePayment, PaymentError = get_classes(
    "payment.exceptions", ["RedirectRequired", "UnableToTakePayment", "PaymentError"]
)
NoShippingRequired = get_class("shipping.methods", "NoShippingRequired")


class CheckoutMixin(object):
    def create_digital_product(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=False
        )
        product = factories.ProductFactory(product_class=product_class)
        factories.StockRecordFactory(
            num_in_stock=None, price=D("12.00"), product=product
        )
        return product

    def add_product_to_basket(self, product=None, **kwargs):
        if product is None:
            product = factories.ProductFactory()
            factories.StockRecordFactory(
                num_in_stock=10, price=D("12.00"), product=product
            )
        detail_page = self.get(
            product.get_absolute_url(), user=kwargs.get("logged_in_user", self.user)
        )
        form = detail_page.forms["add_to_basket_form"]
        form.submit()

    def add_voucher_to_basket(self, voucher=None):
        if voucher is None:
            voucher = factories.create_voucher()
        basket_page = self.get(reverse("basket:summary"))
        form = basket_page.forms["voucher_form"]
        form["code"] = voucher.code
        form.submit()

    def enter_guest_details(self, email="guest@example.com"):
        index_page = self.get(reverse("checkout:index"))
        if index_page.status_code == 200:
            index_page.form["username"] = email
            index_page.form.select("options", GatewayForm.GUEST)
            index_page.form.submit()

    def create_shipping_country(self):
        return factories.CountryFactory(iso_3166_1_a2="GB", is_shipping_country=True)

    def enter_shipping_address(self):
        self.create_shipping_country()
        address_page = self.get(reverse("checkout:shipping-address"))
        if address_page.status_code == 200:
            form = address_page.forms["new_shipping_address"]
            form["first_name"] = "John"
            form["last_name"] = "Doe"
            form["line1"] = "1 Egg Road"
            form["line4"] = "Shell City"
            form["postcode"] = "N12 9RT"
            form.submit()

    def enter_shipping_method(self):
        self.get(reverse("checkout:shipping-method"))

    def place_order(self):
        payment_details = (
            self.get(reverse("checkout:shipping-method")).follow().follow()
        )
        preview = payment_details.click(linkid="view_preview")
        return preview.forms["place_order_form"].submit().follow()

    def reach_payment_details_page(self):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details("hello@egg.com")
        self.enter_shipping_address()
        return self.get(reverse("checkout:shipping-method")).follow().follow()

    def ready_to_place_an_order(self):
        payment_details = self.reach_payment_details_page()
        return payment_details.click(linkid="view_preview")


class IndexViewPreConditionsMixin:
    view_name = None

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    def test_check_basket_is_not_empty(
        self,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, "basket:summary")

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    def test_check_basket_is_valid(
        self,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        # Add product to basket but then remove its stock so it is not
        # purchasable.
        product = factories.ProductFactory()
        self.add_product_to_basket(product)
        product.stockrecords.all().update(num_in_stock=0)
        if self.is_anonymous:
            self.enter_guest_details()

        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, "basket:summary")


class ShippingAddressViewSkipConditionsMixin:
    view_name = None
    next_view_name = None

    def test_skip_unless_basket_requires_shipping(self):
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        if self.is_anonymous:
            self.enter_guest_details()

        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, self.next_view_name)


class ShippingAddressViewPreConditionsMixin(IndexViewPreConditionsMixin):
    view_name = None

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    def test_check_user_email_is_captured(
        self,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        if self.is_anonymous:
            self.add_product_to_basket()
            response = self.get(reverse(self.view_name))
            self.assertRedirectsTo(response, "checkout:index")


class ShippingAddressViewMixin(
    ShippingAddressViewSkipConditionsMixin, ShippingAddressViewPreConditionsMixin
):
    def test_submitting_valid_form_adds_data_to_session(self):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.create_shipping_country()

        page = self.get(reverse("checkout:shipping-address"))
        form = page.forms["new_shipping_address"]
        form["first_name"] = "Barry"
        form["last_name"] = "Chuckle"
        form["line1"] = "1 King Street"
        form["line4"] = "Gotham City"
        form["postcode"] = "N1 7RR"
        response = form.submit()
        self.assertRedirectsTo(response, "checkout:shipping-method")

        session_data = self.app.session["checkout_data"]
        session_fields = session_data["shipping"]["new_address_fields"]
        self.assertEqual("Barry", session_fields["first_name"])
        self.assertEqual("Chuckle", session_fields["last_name"])
        self.assertEqual("1 King Street", session_fields["line1"])
        self.assertEqual("Gotham City", session_fields["line4"])
        self.assertEqual("N1 7RR", session_fields["postcode"])

    def test_shows_initial_data_if_the_form_has_already_been_submitted(self):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        page = self.get(reverse("checkout:shipping-address"), user=self.user)
        form = page.forms["new_shipping_address"]
        self.assertEqual("John", form["first_name"].value)
        self.assertEqual("Doe", form["last_name"].value)
        self.assertEqual("1 Egg Road", form["line1"].value)
        self.assertEqual("Shell City", form["line4"].value)
        self.assertEqual("N12 9RT", form["postcode"].value)


class ShippingMethodViewSkipConditionsMixin:
    view_name = None
    next_view_name = None

    def test_skip_unless_basket_requires_shipping(self):
        # This skip condition is not a "normal" one, but is implemented in the
        # view's "get" method
        product = self.create_digital_product()
        self.add_product_to_basket(product)
        if self.is_anonymous:
            self.enter_guest_details()

        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, self.next_view_name)
        self.assertEqual(
            self.app.session["checkout_data"]["shipping"]["method_code"],
            NoShippingRequired.code,
        )

    @mock.patch("oscar.apps.checkout.views.Repository")
    def test_skip_if_single_shipping_method_is_available(self, mock_repo):
        # This skip condition is not a "normal" one, but is implemented in the
        # view's "get" method
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure one shipping method available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free()]

        response = self.get(reverse("checkout:shipping-method"))
        self.assertRedirectsTo(response, "checkout:payment-method")


class ShippingMethodViewPreConditionsMixin(ShippingAddressViewPreConditionsMixin):
    view_name = None

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    @mock.patch("oscar.apps.checkout.views.Repository")
    def test_check_shipping_methods_are_available(
        self,
        mock_repo,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        # This pre condition is not a "normal" one, but is implemented in the
        # view's "get" method
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure no shipping methods available
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = []

        response = self.get(reverse("checkout:shipping-method"))
        self.assertRedirectsTo(response, "checkout:shipping-address")

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    def test_check_shipping_data_is_captured(
        self,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        # This pre condition is not a "normal" one, but is implemented in the
        # view's "get" method
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()

        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, "checkout:shipping-address")


class ShippingMethodViewMixin(
    ShippingMethodViewSkipConditionsMixin, ShippingMethodViewPreConditionsMixin
):
    @mock.patch("oscar.apps.checkout.views.Repository")
    def test_shows_form_when_multiple_shipping_methods_available(self, mock_repo):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()

        # Ensure multiple shipping methods available
        method = mock.MagicMock()
        method.code = "m"
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free(), method]
        form_page = self.get(reverse("checkout:shipping-method"))
        self.assertIsOk(form_page)

        response = form_page.forms[0].submit()
        self.assertRedirectsTo(response, "checkout:payment-method")

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    @mock.patch("oscar.apps.checkout.views.Repository")
    def test_check_user_can_submit_only_valid_shipping_method(
        self,
        mock_repo,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        method = mock.MagicMock()
        method.code = "m"
        instance = mock_repo.return_value
        instance.get_shipping_methods.return_value = [methods.Free(), method]
        form_page = self.get(reverse("checkout:shipping-method"))
        # a malicious attempt?
        form_page.forms[0]["method_code"].value = "super-free-shipping"
        response = form_page.forms[0].submit()
        self.assertIsNotRedirect(response)
        response.mustcontain("Your submitted shipping method is not permitted")


class PaymentMethodViewSkipConditionsMixin:
    @mock.patch("oscar.apps.checkout.session.SurchargeApplicator.get_surcharges")
    def test_skip_unless_payment_is_required(self, mock_get_surcharges):
        mock_get_surcharges.return_value = []

        product = factories.create_product(price=D("0.00"), num_in_stock=100)
        self.add_product_to_basket(product)
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        # The shipping method is set automatically, as there is only one (free)
        # available

        response = self.get(reverse("checkout:payment-method"))
        self.assertRedirectsTo(response, "checkout:preview")


class PaymentMethodViewPreConditionsMixin(ShippingMethodViewPreConditionsMixin):
    view_name = None

    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    def test_check_shipping_data_is_captured(
        self,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        super().test_check_shipping_data_is_captured()

        self.enter_shipping_address()

        response = self.get(reverse(self.view_name))
        self.assertRedirectsTo(response, "checkout:shipping-method")


class PaymentMethodViewMixin(
    PaymentMethodViewSkipConditionsMixin, PaymentMethodViewPreConditionsMixin
):
    pass


class PaymentDetailsViewSkipConditionsMixin:
    @mock.patch("oscar.apps.checkout.session.SurchargeApplicator.get_surcharges")
    def test_skip_unless_payment_is_required(self, mock_get_surcharges):
        mock_get_surcharges.return_value = []

        product = factories.create_product(price=D("0.00"), num_in_stock=100)
        self.add_product_to_basket(product)
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        # The shipping method is set automatically, as there is only one (free)
        # available

        response = self.get(reverse("checkout:payment-details"))
        self.assertRedirectsTo(response, "checkout:preview")


class PaymentDetailsViewPreConditionsMixin(PaymentMethodViewPreConditionsMixin):
    """
    Does not add any new pre conditions.
    """


class PaymentDetailsViewMixin(
    PaymentDetailsViewSkipConditionsMixin, PaymentDetailsViewPreConditionsMixin
):
    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_payment")
    def test_redirects_customers_when_using_bank_gateway(self, mock_method):
        bank_url = "https://bank-website.com"
        e = RedirectRequired(url=bank_url)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order()
        bank_redirect = preview.forms["place_order_form"].submit()

        assert bank_redirect.status_code == 302
        assert bank_redirect.url == bank_url

    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_payment")
    def test_handles_anticipated_payments_errors_gracefully(self, mock_method):
        msg = "Submitted expiration date is wrong"
        e = UnableToTakePayment(msg)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order()
        response = preview.forms["place_order_form"].submit()
        self.assertIsOk(response)
        # check user is warned
        response.mustcontain(msg)
        # check basket is restored
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch("oscar.apps.checkout.views.logger")
    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_payment")
    def test_handles_unexpected_payment_errors_gracefully(
        self, mock_method, mock_logger
    ):
        msg = "This gateway is down for maintenance"
        e = PaymentError(msg)
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order()
        response = preview.forms["place_order_form"].submit()
        self.assertIsOk(response)
        # check user is warned with a generic error
        response.mustcontain(
            "A problem occurred while processing payment for this order", no=[msg]
        )
        # admin should be warned
        self.assertTrue(mock_logger.error.called)
        # check basket is restored
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch("oscar.apps.checkout.views.logger")
    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_payment")
    def test_handles_bad_errors_during_payments(self, mock_method, mock_logger):
        e = Exception()
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order()
        response = preview.forms["place_order_form"].submit()
        self.assertIsOk(response)
        self.assertTrue(mock_logger.exception.called)
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch("oscar.apps.checkout.views.logger")
    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_order_placement")
    def test_handles_unexpected_order_placement_errors_gracefully(
        self, mock_method, mock_logger
    ):
        e = UnableToPlaceOrder()
        mock_method.side_effect = e
        preview = self.ready_to_place_an_order()
        response = preview.forms["place_order_form"].submit()
        self.assertIsOk(response)
        self.assertTrue(mock_logger.error.called)
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)

    @mock.patch("oscar.apps.checkout.views.logger")
    @mock.patch("oscar.apps.checkout.views.PaymentDetailsView.handle_order_placement")
    def test_handles_all_other_exceptions_gracefully(self, mock_method, mock_logger):
        mock_method.side_effect = Exception()
        preview = self.ready_to_place_an_order()
        response = preview.forms["place_order_form"].submit()
        self.assertIsOk(response)
        self.assertTrue(mock_logger.exception.called)
        basket = Basket.objects.get()
        self.assertEqual(basket.status, Basket.OPEN)


class PaymentDetailsPreviewViewPreConditionsMixin(PaymentDetailsViewPreConditionsMixin):
    # Disable skip conditions, so that we do not first get redirected forwards
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_payment_is_required"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.skip_unless_basket_requires_shipping"
    )
    @mock.patch(
        "oscar.apps.checkout.session.CheckoutSessionMixin.check_payment_data_is_captured"
    )
    def test_check_payment_data_is_captured(
        self,
        mock_check_payment_data_is_captured,
        mock_skip_unless_basket_requires_shipping,
        mock_skip_unless_payment_is_required,
    ):
        mock_check_payment_data_is_captured.side_effect = FailedPreCondition(
            url=reverse("checkout:payment-details")
        )
        response = self.ready_to_place_an_order()
        self.assertRedirectsTo(response, "checkout:payment-details")


class PaymentDetailsPreviewViewMixin(PaymentDetailsPreviewViewPreConditionsMixin):
    def test_allows_order_to_be_placed(self):
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()

        payment_details = (
            self.get(reverse("checkout:shipping-method")).follow().follow()
        )
        preview = payment_details.click(linkid="view_preview")
        preview.forms["place_order_form"].submit().follow()

        self.assertEqual(1, Order.objects.all().count())

    def test_payment_form_being_submitted_from_payment_details_view(self):
        payment_details = self.reach_payment_details_page()
        preview = payment_details.forms["sensible_data"].submit()
        self.assertEqual(0, Order.objects.all().count())
        preview.form.submit().follow()
        self.assertEqual(1, Order.objects.all().count())

    def test_handles_invalid_payment_forms(self):
        payment_details = self.reach_payment_details_page()
        form = payment_details.forms["sensible_data"]
        # payment forms should use the preview URL not the payment details URL
        form.action = reverse("checkout:payment-details")
        self.assertEqual(form.submit(status="*").status_code, http_client.BAD_REQUEST)

    def test_placing_an_order_using_a_voucher_records_use(self):
        self.add_product_to_basket()
        self.add_voucher_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        thankyou = self.place_order()

        order = thankyou.context["order"]
        self.assertEqual(1, order.discounts.all().count())

        discount = order.discounts.all()[0]
        voucher = discount.voucher
        self.assertEqual(1, voucher.num_orders)

    def test_placing_an_order_using_an_offer_records_use(self):
        offer = factories.create_offer()
        self.add_product_to_basket()
        if self.is_anonymous:
            self.enter_guest_details()
        self.enter_shipping_address()
        self.place_order()

        # Reload offer
        offer = ConditionalOffer.objects.get(id=offer.id)

        self.assertEqual(1, offer.num_orders)
        self.assertEqual(1, offer.num_applications)
