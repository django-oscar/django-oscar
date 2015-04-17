from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from oscar.apps.shipping.methods import NoShippingRequired
from oscar.core.loading import get_class

from . import signals

OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
RedirectRequired = get_class('checkout.mixins', 'RedirectRequired')
CheckoutFailed = get_class('checkout.mixins', 'CheckoutFailed')


class CheckoutFlow(OrderPlacementMixin):
    def checkout(self):
        """
        Manage the checkout flow.

        This mixin doesn't do any of the hard work; instead it delegates to
        specialized views that are responsible for a certain task.

        This method is the entry point for the checkout process through the
        `IndexView`. It is also the resumption point for views that perform
        checkout-related tasks. Such views call this method after performing
        their work to return control here.

        This method never produces an answer that is not a redirect, so it is
        ok to call it from a POST request directly instead of redirecting do
        checkout:index.
        """
        try:
            self.do_checkout()
        except RedirectRequired as e:
            return redirect(e.target)
        except CheckoutFailed as e:
            return self.checkout_failed()

        return self.checkout_successful()

    def do_checkout(self, *args, **kwargs):
        """
        Perform the checkout steps in order. Each step is either complete, then
        the function just returns. Or it raises RedirectRequired to redirect to
        a view that implements the step. The steps are:

            1. Identify the user (`identify_user`)
            2. Send start_checkout signal (`send_start_checkout_signal`)
            3. Capture shipping information (`capture_shipping_data`)
            4. Capture payment information (`capture_payment_data`)
            5. Get final order confirmation (`confirm_order_preview`)
            6. Finally, conduct payment and place order (`submit_order`)

        The last step can raise CheckoutFailed to initiate a retry.
        """
        basket = self.request.basket

        self.check_basket(basket)
        self.identify_user()
        self.send_start_checkout_signal()

        shipping_method, shipping_address = self.capture_shipping_data(basket)

        shipping_charge = shipping_method.calculate(basket)
        self.capture_payment_data(basket, shipping_charge)

        self.confirm_order_preview()
        self.submit_order()

    def checkout_failed(self):
        """
        Also, call this from the result view after a redirect payment.
        """
        # try again
        self.checkout_session.reset_preview_confirmation()
        return self.checkout()

    def checkout_successful(self):
        """
        Also, call this from the result view after a redirect payment.
        """
        self.checkout_session.flush()
        return redirect('checkout:thank-you')

    def check_basket(self, basket):
        """
        Check that the basket is ready for submission.
        """
        if basket.is_empty:
            messages.warning(self.request, _(
                "You need to add some items to your basket to checkout"))
            raise RedirectRequired('basket:summary')

        if not self.check_basket_available(basket):
            raise RedirectRequired('basket:summary')

    def identify_user(self):
        # get guest checkout email or login
        if not self.request.user.is_authenticated():
            if not self.checkout_session.get_guest_email():
                raise RedirectRequired('checkout:identify-user')

    def send_start_checkout_signal(self):
        if not self.checkout_session.was_start_checkout_signal_sent():
            if self.checkout_session.get_guest_email():
                signals.start_checkout.send_robust(
                    sender=self, request=self.request,
                    email=self.checkout_session.get_guest_email())
            else:
                signals.start_checkout.send_robust(
                    sender=self, request=self.request)

            self.checkout_session.set_sent_start_checkout_signal()

    def capture_shipping_data(self, basket):
        # capture shipping method and address
        if not basket.is_shipping_required():
            shipping_method = NoShippingRequired()
            self.checkout_session.use_shipping_method(
                shipping_method.code)
            return shipping_method, None

        if not self.checkout_session.is_shipping_address_set():
            raise RedirectRequired('checkout:shipping-address')

        # Check that the previously chosen shipping address is still valid
        shipping_address = self.get_shipping_address(basket)
        if not shipping_address:
            messages.warning(self.request,
                             _("Your previously chosen shipping address is no "
                               "longer valid.  Please choose another one"))
            raise RedirectRequired('checkout:shipping-address')

        if not self.checkout_session.is_shipping_method_set(basket):
            methods = self.get_available_shipping_methods(
                basket, shipping_address)

            if len(methods) == 0:
                # No shipping methods available for given address
                messages.warning(self.request, _(
                    "Shipping is unavailable for your chosen address - "
                    "please choose another"))
                raise RedirectRequired('checkout:shipping-address')

            elif len(methods) == 1:
                # Only one shipping method - use it
                self.checkout_session.use_shipping_method(methods[0].code)

            else:
                # Must be more than one available shipping method, we
                # present them to the user to make a choice.
                raise RedirectRequired('checkout:shipping-method')

        shipping_method = self.get_shipping_method(basket, shipping_address)
        if not shipping_method:
            messages.warning(self.request,
                             _("Your previously chosen shipping method is no "
                               "longer valid.  Please choose another one"))
            raise RedirectRequired('checkout:shipping-method')

        return shipping_method, shipping_address

    def capture_payment_data(self, basket, shipping_charge):
        total = self.get_order_totals(basket, shipping_charge)

        if total.excl_tax > 0:
            if not self.check_payment_data_is_captured():
                raise RedirectRequired('checkout:payment-details')

    def confirm_order_preview(self):
        if not self.checkout_session.was_preview_confirmed():
            raise RedirectRequired('checkout:preview')

    def submit_order(self):
        return self.submit_basket(**self.build_submission())

    # Helpers

    def check_basket_available(self, basket):
        """
        Check that the basket is permitted to be submitted as an order. That
        is, all the basket lines are available to buy - nothing has gone out of
        stock since it was added to the basket.
        """
        can_submit, errors = basket.check_all_lines_available()
        if can_submit:
            return True

        for (line, reason) in errors:
            # Create a more meaningful message to show on the basket page
            msg = _(
                "'%(title)s' is no longer available to buy (%(reason)s). "
                "Please adjust your basket to continue"
            ) % {
                'title': line.product.get_title(),
                'reason': reason}
            messages.warning(self.request, msg)

        return False

    def check_payment_data_is_captured(self):
        # We don't collect payment data by default so we don't have anything to
        # validate here. If your shop requires forms to be submitted on the
        # payment details page, then override this method to check that the
        # relevant data is available.
        return True
