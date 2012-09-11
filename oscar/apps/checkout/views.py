import logging

from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import get_model
from django.utils.translation import ugettext as _
from django.views.generic import DetailView, TemplateView, FormView, \
                                 DeleteView, UpdateView, CreateView

from oscar.apps.shipping.methods import NoShippingRequired
from oscar.core.loading import get_class, get_classes
ShippingAddressForm, GatewayForm = get_classes('checkout.forms', ['ShippingAddressForm', 'GatewayForm'])
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')
CheckoutSessionData = get_class('checkout.utils', 'CheckoutSessionData')
pre_payment, post_payment = get_classes('checkout.signals', ['pre_payment', 'post_payment'])
OrderNumberGenerator, OrderCreator = get_classes('order.utils', ['OrderNumberGenerator', 'OrderCreator'])
UserAddressForm = get_class('address.forms', 'UserAddressForm')
Repository = get_class('shipping.repository', 'Repository')
AccountAuthView = get_class('customer.views', 'AccountAuthView')
Dispatcher = get_class('customer.utils', 'Dispatcher')
RedirectRequired, UnableToTakePayment, PaymentError = get_classes(
    'payment.exceptions', ['RedirectRequired', 'UnableToTakePayment', 'PaymentError'])
UnableToPlaceOrder = get_class('order.exceptions', 'UnableToPlaceOrder')
OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')

Order = get_model('order', 'Order')
ShippingAddress = get_model('order', 'ShippingAddress')
CommunicationEvent = get_model('order', 'CommunicationEvent')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentEvent = get_model('order', 'PaymentEvent')
UserAddress = get_model('address', 'UserAddress')
Basket = get_model('basket', 'Basket')
Email = get_model('customer', 'Email')
CommunicationEventType = get_model('customer', 'CommunicationEventType')

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class IndexView(CheckoutSessionMixin, FormView):
    """
    First page of the checkout.  We prompt user to either sign in, or
    to proceed as a guest (where we still collect their email address).
    """
    template_name = 'checkout/gateway.html'
    form_class = GatewayForm

    def get(self, request, *args, **kwargs):
        # We redirect immediately to shipping address stage if the user is signed in or
        # has already filled out the anonymous checkout form.
        if request.user.is_authenticated() or self.checkout_session.get_guest_email():
            return self.get_success_response()
        return super(IndexView, self).get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(IndexView, self).get_form_kwargs()
        email = self.checkout_session.get_guest_email()
        if email:
            kwargs['initial'] = {
                'username': email,
                'options': 'new'
            }
        return kwargs

    def form_valid(self, form):
        if form.is_guest_checkout():
            email = form.cleaned_data['username']
            self.checkout_session.set_guest_email(email)
        else:
            user = form.get_user()
            login(self.request, user)
        return self.get_success_response()

    def get_success_response(self):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('checkout:shipping-address')


# ================
# SHIPPING ADDRESS
# ================


class ShippingAddressView(CheckoutSessionMixin, FormView):
    """
    Determine the shipping address for the order.

    The default behaviour is to display a list of addresses from the users's
    address book, from which the user can choose one to be their shipping address.
    They can add/edit/delete these USER addresses.  This address will be
    automatically converted into a SHIPPING address when the user checks out.

    Alternatively, the user can enter a SHIPPING address directly which will be
    saved in the session and later saved as ShippingAddress model when the order
    is sucessfully submitted.
    """
    template_name = 'checkout/shipping_address.html'
    form_class = ShippingAddressForm

    def get(self, request, *args, **kwargs):
        # Check that the user's basket is not empty
        if request.basket.is_empty:
            messages.error(request, _("You need to add some items to your basket to checkout"))
            return HttpResponseRedirect(reverse('basket:summary'))

        # Check that guests have entered an email address
        if not request.user.is_authenticated() and not self.checkout_session.get_guest_email():
            messages.error(request, _("Please either sign in or enter your email address"))
            return HttpResponseRedirect(reverse('checkout:index'))

        # Check to see that a shipping address is actually required.  It may not be if
        # the basket is purely downloads
        if not request.basket.is_shipping_required():
            messages.info(request, _("Your basket does not require a shipping address to be submitted"))
            return HttpResponseRedirect(self.get_success_url())

        return super(ShippingAddressView, self).get(request, *args, **kwargs)

    def get_initial(self):
        return self.checkout_session.new_shipping_address_fields()

    def get_context_data(self, **kwargs):
        kwargs = super(ShippingAddressView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            # Look up address book data
            kwargs['addresses'] = self.get_available_addresses()
        return kwargs

    def get_available_addresses(self):
        return UserAddress._default_manager.filter(user=self.request.user).order_by('-is_default_for_shipping')

    def post(self, request, *args, **kwargs):
        # Check if a shipping address was selected directly (eg no form was filled in)
        if self.request.user.is_authenticated() and 'address_id' in self.request.POST:
            address = UserAddress._default_manager.get(pk=self.request.POST['address_id'],
                                                       user=self.request.user)
            action = self.request.POST.get('action', None)
            if action == 'ship_to':
                # User has selected a previous address to ship to
                self.checkout_session.ship_to_user_address(address)
                return HttpResponseRedirect(self.get_success_url())
            elif action == 'delete':
                # Delete the selected address
                address.delete()
                messages.info(self.request, _("Address deleted from your address book"))
                return HttpResponseRedirect(reverse('checkout:shipping-method'))
            else:
                return HttpResponseBadRequest()
        else:
            return super(ShippingAddressView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        # Store the address details in the session and redirect to next step
        self.checkout_session.ship_to_new_address(form.clean())
        return super(ShippingAddressView, self).form_valid(form)

    def get_success_url(self):
        return reverse('checkout:shipping-method')


class UserAddressCreateView(CheckoutSessionMixin, CreateView):
    """
    Add a USER address to the user's addressbook.

    This is not the same as creating a SHIPPING Address, although if used for the order,
    it will be converted into a shipping address at submission-time.
    """
    template_name = 'checkout/user_address_form.html'
    form_class = UserAddressForm

    def get_context_data(self, **kwargs):
        kwargs = super(UserAddressCreateView, self).get_context_data(**kwargs)
        kwargs['form_url'] = reverse('checkout:user-address-create')
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return self.get_success_response()

    def get_success_response(self):
        messages.info(self.request, _("Address saved"))
        # We redirect back to the shipping address page
        return HttpResponseRedirect(reverse('checkout:shipping-address'))


class UserAddressUpdateView(CheckoutSessionMixin, UpdateView):
    """
    Update a user address
    """
    template_name = 'checkout/user_address_form.html'
    form_class = UserAddressForm

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        kwargs = super(UserAddressUpdateView, self).get_context_data(**kwargs)
        kwargs['form_url'] = reverse('checkout:user-address-update', args=(str(kwargs['object'].id),))
        return kwargs

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return reverse('checkout:shipping-address')


class UserAddressDeleteView(CheckoutSessionMixin, DeleteView):
    """
    Delete an address from a user's addressbook.
    """
    template_name = 'checkout/user_address_delete.html'

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.info(self.request, _("Address deleted"))
        return reverse('checkout:shipping-address')


# ===============
# Shipping method
# ===============


class ShippingMethodView(CheckoutSessionMixin, TemplateView):
    """
    View for allowing a user to choose a shipping method.

    Shipping methods are largely domain-specific and so this view
    will commonly need to be subclassed and customised.

    The default behaviour is to load all the available shipping methods
    using the shipping Repository.  If there is only 1, then it is
    automatically selected.  Otherwise, a page is rendered where
    the user can choose the appropriate one.
    """
    template_name = 'checkout/shipping_methods.html'

    def get(self, request, *args, **kwargs):
        # Check that the user's basket is not empty
        if request.basket.is_empty:
            messages.error(request, _("You need to add some items to your basket to checkout"))
            return HttpResponseRedirect(reverse('basket:summary'))

        # Check that shipping is required at all
        if not request.basket.is_shipping_required():
            self.checkout_session.use_shipping_method(NoShippingRequired().code)
            return self.get_success_response()

        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            messages.error(request, _("Please choose a shipping address"))
            return HttpResponseRedirect(reverse('checkout:shipping-address'))

        # Save shipping methods as instance var as we need them both here
        # and when setting the context vars.
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 0:
            # No shipping methods available for given address
            messages.warning(request, _("Shipping is not available for your chosen address - please choose another"))
            return HttpResponseRedirect(reverse('checkout:shipping-address'))
        elif len(self._methods) == 1:
            # Only one shipping method - set this and redirect onto the next step
            self.checkout_session.use_shipping_method(self._methods[0].code)
            return self.get_success_response()

        # Must be more than one available shipping method, we present them to
        # the user to make a choice.
        return super(ShippingMethodView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ShippingMethodView, self).get_context_data(**kwargs)
        kwargs['methods'] = self._methods
        return kwargs

    def get_available_shipping_methods(self):
        """
        Returns all applicable shipping method objects
        for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address.  I haven't come across a scenario that doesn't
        # fit this system.
        return Repository().get_shipping_methods(self.request.user, self.request.basket,
                                                 self.get_shipping_address())

    def post(self, request, *args, **kwargs):
        # Need to check that this code is valid for this user
        method_code = request.POST.get('method_code', None)
        is_valid = False
        for method in self.get_available_shipping_methods():
            if method.code == method_code:
                is_valid = True
        if not is_valid:
            messages.error(request, _("Your submitted shipping method is not permitted"))
            return HttpResponseRedirect(reverse('checkout:shipping-method'))

        # Save the code for the chosen shipping method in the session
        # and continue to the next step.
        self.checkout_session.use_shipping_method(method_code)
        return self.get_success_response()

    def get_success_response(self):
        return HttpResponseRedirect(reverse('checkout:payment-method'))


# ==============
# Payment method
# ==============


class PaymentMethodView(CheckoutSessionMixin, TemplateView):
    """
    View for a user to choose which payment method(s) they want to use.

    This would include setting allocations if payment is to be split
    between multiple sources.
    """

    def get(self, request, *args, **kwargs):
        # Check that the user's basket is not empty
        if request.basket.is_empty:
            messages.error(request, _("You need to add some items to your basket to checkout"))
            return HttpResponseRedirect(reverse('basket:summary'))

        shipping_required = request.basket.is_shipping_required()

        # Check that shipping address has been completed
        if shipping_required and not self.checkout_session.is_shipping_address_set():
            messages.error(request, _("Please choose a shipping address"))
            return HttpResponseRedirect(reverse('checkout:shipping-address'))

        # Check that shipping method has been set
        if shipping_required and not self.checkout_session.is_shipping_method_set():
            messages.error(request, _("Please choose a shipping method"))
            return HttpResponseRedirect(reverse('checkout:shipping-method'))

        return self.get_success_response()

    def get_success_response(self):
        return HttpResponseRedirect(reverse('checkout:payment-details'))


# ================
# Order submission
# ================


class PaymentDetailsView(OrderPlacementMixin, TemplateView):
    """
    For taking the details of payment and creating the order

    The class is deliberately split into fine-grained methods, responsible for only one
    thing.  This is to make it easier to subclass and override just one component of
    functionality.

    All projects will need to subclass and customise this class.
    """
    template_name = 'checkout/payment_details.html'
    template_name_preview = 'checkout/preview.html'
    preview = False

    def get_template_names(self):
        return [self.template_name_preview] if self.preview else [self.template_name]

    def get_error_response(self):
        # Check that the user's basket is not empty
        if self.request.basket.is_empty:
            messages.error(self.request, _("You need to add some items to your basket to checkout"))
            return HttpResponseRedirect(reverse('basket:summary'))

        shipping_required = self.request.basket.is_shipping_required()
        # Check that shipping address has been completed
        if shipping_required and not self.checkout_session.is_shipping_address_set():
            messages.error(self.request, _("Please choose a shipping address"))
            return HttpResponseRedirect(reverse('checkout:shipping-address'))
        # Check that shipping method has been set
        if shipping_required and not self.checkout_session.is_shipping_method_set():
            messages.error(self.request, _("Please choose a shipping method"))
            return HttpResponseRedirect(reverse('checkout:shipping-method'))

    def get(self, request, *args, **kwargs):
        error_response = self.get_error_response()
        if error_response:
            return error_response
        return super(PaymentDetailsView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        This method is designed to be overridden by subclasses which will
        validate the forms from the payment details page.  If the forms are valid
        then the method can call submit()
        """
        error_response = self.get_error_response()

        if error_response:
            return error_response
        if self.preview:
            # We use a custom parameter to indicate if this is an attempt to place an order.
            # Without this, we assume a payment form is being submitted from the
            # payment-details page
            if request.POST.get('action', '') == 'place_order':
                return self.submit(request.basket)
            return self.render_preview(request)

        # Posting to payment-details isn't the right thing to do
        return self.get(request, *args, **kwargs)

    def render_preview(self, request, **kwargs):
        """
        Show a preview of the order.

        If sensitive data was submitted on the payment details page, you will
        need to pass it back to the view here so it can be stored in hidden form
        inputs.  This avoids ever writing the sensitive data to disk.
        """
        ctx = self.get_context_data()
        ctx.update(kwargs)
        return self.render_to_response(ctx)

    def can_basket_be_submitted(self, basket):
        for line in basket.lines.all():
            is_permitted, reason = line.product.is_purchase_permitted(self.request.user, line.quantity)
            if not is_permitted:
                return False, reason, reverse('basket:summary')
        return True, None, None

    def get_default_billing_address(self):
        """
        Return default billing address for user

        This is useful when the payment details view includes a billing address
        form - you can use this helper method to prepopulate the form.

        Note, this isn't used in core oscar as there is no billing address form
        by default.
        """
        if not self.request.user.is_authenticated():
            return None
        try:
            return self.request.user.addresses.get(is_default_for_billing=True)
        except UserAddress.DoesNotExist:
            return None

    def submit(self, basket, payment_kwargs=None, order_kwargs=None):
        """
        Submit a basket for order placement.

        The process runs as follows:
         * Generate an order number
         * Freeze the basket so it cannot be modified any more (important when
           redirecting the user to another site for payment as it prevents the
           basket being manipulated during the payment process).
         * Attempt to take payment for the order
           - If payment is successful, place the order
           - If a redirect is required (eg PayPal, 3DSecure), redirect
           - If payment is unsuccessful, show an appropriate error message

        :basket: The basket to submit.
        :payment_kwargs: Additional kwargs to pass to the handle_payment method.
        :order_kwargs: Additional kwargs to pass to the place_order method.
        """
        if payment_kwargs is None:
            payment_kwargs = {}
        if order_kwargs is None:
            order_kwargs = {}

        # Next, check that basket isn't empty
        if basket.is_empty:
            messages.error(self.request, _("This order cannot be submitted as the basket is empty"))
            url = self.request.META.get('HTTP_REFERER', reverse('basket:summary'))
            return HttpResponseRedirect(url)

        # Domain-specific checks on the basket
        is_valid, reason, url = self.can_basket_be_submitted(basket)
        if not is_valid:
            messages.error(self.request, reason)
            return HttpResponseRedirect(url)

        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been
        # created).  We also save it in the session for multi-stage
        # checkouts (eg where we redirect to a 3rd party site and place
        # the order on a different request).
        order_number = self.generate_order_number(basket)
        logger.info("Order #%s: beginning submission process for basket #%d", order_number, basket.id)

        # Freeze the basket so it cannot be manipulated while the customer is
        # completing payment on a 3rd party site.  Also, store a reference to
        # the basket in the session so that we know which basket to thaw if we
        # get an unsuccessful payment response when redirecting to a 3rd party
        # site.
        self.freeze_basket(basket)
        self.checkout_session.set_submitted_basket(basket)

        # Handle payment.  Any payment problems should be handled by the
        # handle_payment method raise an exception, which should be caught
        # within handle_POST and the appropriate forms redisplayed.
        error_msg = _("A problem occurred while processing payment for this "
                      "order.  No payment has been taken.  Please try again "
                      "contact customer services if this problem persists")
        pre_payment.send_robust(sender=self, view=self)
        total_incl_tax, total_excl_tax = self.get_order_totals(basket)
        try:
            self.handle_payment(order_number, total_incl_tax, **payment_kwargs)
        except RedirectRequired, e:
            # Redirect required (eg PayPal, 3DS)
            logger.info("Order #%s: redirecting to %s", order_number, e.url)
            return HttpResponseRedirect(e.url)
        except UnableToTakePayment, e:
            # Something went wrong with payment but in an anticipated way.  Eg
            # their bankcard has expired, wrong card number - that kind of
            # thing. This type of exception is supposed to set a friendly error
            # message that makes sense to the customer.
            msg = unicode(e)
            logger.warning("Order #%s: unable to take payment (%s) - restoring basket", order_number, msg)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=msg))
        except PaymentError, e:
            # A general payment error - Something went wrong which wasn't
            # anticipated.  Eg, the payment gateway is down (it happens), your
            # credentials are wrong - that king of thing.
            # It makes sense to configure the checkout logger to
            # mail admins on an error as this issue warrants some further
            # investigation.
            msg = unicode(e)
            logger.error("Order #%s: payment error (%s)", order_number, msg)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=error_msg))
        except Exception, e:
            # Unhandled exception - hopefully, you will only ever see this in
            # development.
            logger.error("Order #%s: unhandled exception while taking payment (%s)", order_number, e)
            logger.exception(e)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=error_msg))
        post_payment.send_robust(sender=self, view=self)

        # If all is ok with payment, try and place order
        logger.info("Order #%s: payment successful, placing order", order_number)
        try:
            return self.handle_order_placement(order_number, basket,
                                               total_incl_tax, total_excl_tax,
                                               **order_kwargs)
        except UnableToPlaceOrder, e:
            # It's possible that something will go wrong while trying to
            # actually place an order.  Not a good situation to be in, but needs
            # to be handled gracefully.
            logger.error("Order #%s: unable to place order - %s", order_number, e)
            msg = unicode(e)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=msg))

    def generate_order_number(self, basket):
        generator = OrderNumberGenerator()
        order_number = generator.order_number(basket)
        self.checkout_session.set_order_number(order_number)
        return order_number

    def freeze_basket(self, basket):
        # We freeze the basket to prevent it being modified once the payment
        # process has started.  If your payment fails, then the basket will
        # need to be "unfrozen".  We also store the basket ID in the session
        # so the it can be retrieved by multistage checkout processes.
        basket.freeze()

    def handle_payment(self, order_number, total, **kwargs):
        """
        Handle any payment processing and record payment sources and events.

        This method is designed to be overridden within your project.  The
        default is to do nothing as payment is domain-specific.

        This method is responsible for handling payment and recording the
        payment sources (using the add_payment_source method) and payment
        events (using add_payment_event) so they can be
        linked to the order when it is saved later on.
        """
        pass

    def get_context_data(self, **kwargs):
        # Return kwargs directly instead of using 'params' as in django's TemplateView
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)
        ctx.update(kwargs)
        return ctx


# =========
# Thank you
# =========


class ThankYouView(DetailView):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """
    template_name = 'checkout/thank_you.html'
    context_object_name = 'order'

    def get_object(self):
        # We allow superusers to force an order thankyou page for testing
        order = None
        if self.request.user.is_superuser:
            if 'order_number' in self.request.GET:
                order = Order._default_manager.get(number=self.request.GET['order_number'])
            elif 'order_id' in self.request.GET:
                order = Order._default_manager.get(id=self.request.GET['orderid'])

        if not order:
            if 'checkout_order_id' in self.request.session:
                order = Order._default_manager.get(pk=self.request.session['checkout_order_id'])
            else:
                raise Http404(_("No order found"))

        return order
