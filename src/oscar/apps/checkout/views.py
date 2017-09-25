import logging

from django import http
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views import generic

from oscar.core.loading import get_class, get_classes, get_model

ShippingAddressForm, GatewayForm \
    = get_classes('checkout.forms', ['ShippingAddressForm', 'GatewayForm'])
UserAddressForm = get_class('address.forms', 'UserAddressForm')
CheckoutFlow = get_class('checkout.flow', 'CheckoutFlow')

Order = get_model('order', 'Order')
UserAddress = get_model('address', 'UserAddress')
Country = get_model('address', 'Country')

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class IndexView(CheckoutFlow, generic.View):
    def get(self, request, *args, **kwargs):
        return self.checkout()


class IdentifyUserView(CheckoutFlow, generic.FormView):
    """
    Identify the user for checkout.  We prompt user to either sign in, or
    to proceed as a guest (where we still collect their email address).

    Checkout responsibilities:
        * set guest email in checkout session
        * or login user
        * or delegate (e.g. to user registration)
    """
    template_name = 'checkout/gateway.html'
    form_class = GatewayForm

    def get_form_kwargs(self):
        kwargs = super(IdentifyUserView, self).get_form_kwargs()
        email = self.checkout_session.get_guest_email()
        if email:
            kwargs['initial'] = {
                'username': email,
            }
        return kwargs

    def form_valid(self, form):
        email = form.cleaned_data['username']

        if form.is_guest_checkout():
            self.checkout_session.set_guest_email(email)

        elif form.is_new_account_checkout():
            # remember guest email if customer decides to abort registration
            # and checkout as a guest
            self.checkout_session.set_guest_email(email)

            messages.info(
                self.request,
                _("Create your account and then you will be redirected "
                  "back to the checkout process"))
            return redirect("%s?next=%s&email=%s" % (
                reverse('customer:register'),
                reverse('checkout:index'),
                urlquote(email)
            ))
        else:
            user = form.get_user()
            login(self.request, user)

        return self.checkout()


# ================
# SHIPPING ADDRESS
# ================


class ShippingAddressView(CheckoutFlow, generic.FormView):
    """
    Determine the shipping address for the order.

    The default behaviour is to display a list of addresses from the users's
    address book, from which the user can choose one to be their shipping
    address.  They can add/edit/delete these USER addresses.  This address will
    be automatically converted into a SHIPPING address when the user checks
    out.

    Alternatively, the user can enter a SHIPPING address directly which will be
    saved in the session and later saved as ShippingAddress model when the
    order is successfully submitted.

    Checkout responsibilities:
        * set shipping address in checkout session
    """
    template_name = 'checkout/shipping_address.html'
    form_class = ShippingAddressForm

    def get_initial(self):
        initial = self.checkout_session.new_shipping_address_fields()
        if initial:
            # Convert the primary key stored in the session into a Country
            # instance
            try:
                initial['country'] = Country.objects.get(
                    iso_3166_1_a2=initial.pop('country_id'))
            except Country.DoesNotExist:
                # Hmm, the previously selected Country no longer exists. We
                # ignore this.
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super(ShippingAddressView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            # Look up address book data
            ctx['addresses'] = self.get_available_addresses()
        return ctx

    def get_available_addresses(self):
        # Include only addresses where the country is flagged as valid for
        # shipping. Also, use ordering to ensure the default address comes
        # first.
        return self.request.user.addresses.order_by(
            '-is_default_for_shipping')

    def post(self, request, *args, **kwargs):
        # Check if a shipping address was selected directly (eg no form was
        # filled in)
        if self.request.user.is_authenticated() \
                and 'address_id' in self.request.POST:
            address = UserAddress._default_manager.get(
                pk=self.request.POST['address_id'], user=self.request.user)
            action = self.request.POST.get('action', None)
            if action == 'ship_to':
                # User has selected a previous address to ship to
                self.checkout_session.ship_to_user_address(address)
                return self.checkout()
            else:
                return http.HttpResponseBadRequest()
        else:
            return super(ShippingAddressView, self).post(
                request, *args, **kwargs)

    def form_valid(self, form):
        # Store the address details in the session and redirect to next step
        address_fields = dict(
            (k, v) for (k, v) in form.instance.__dict__.items()
            if not k.startswith('_'))
        self.checkout_session.ship_to_new_address(address_fields)
        return self.checkout()


class UserAddressUpdateView(CheckoutFlow, generic.UpdateView):
    """
    Update a user address
    """
    template_name = 'checkout/user_address_form.html'
    form_class = UserAddressForm
    success_url = reverse_lazy('checkout:shipping-address')

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_form_kwargs(self):
        kwargs = super(UserAddressUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super(UserAddressUpdateView, self).get_success_url()


class UserAddressDeleteView(CheckoutFlow, generic.DeleteView):
    """
    Delete an address from a user's addressbook.
    """
    template_name = 'checkout/user_address_delete.html'
    success_url = reverse_lazy('checkout:shipping-address')

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.info(self.request, _("Address deleted"))
        return super(UserAddressDeleteView, self).get_success_url()


# ================
# Order submission
# ================

class PaymentDetailsView(CheckoutFlow, generic.TemplateView):
    """
    For taking the details of payment and creating the order.

    This view class is used by two separate URLs: 'payment-details' and
    'preview'. The `preview` class attribute is used to distinguish which is
    being used. Chronologically, `payment-details` (preview=False) comes before
    `preview` (preview=True).

    If sensitive details are required (eg a bankcard), then the payment details
    view should submit to the preview URL and a custom implementation of
    `validate_payment_submission` should be provided.

    - If the form data is valid, then the preview template can be rendered with
      the payment-details forms re-rendered within a hidden div so they can be
      re-submitted when the 'place order' button is clicked. This avoids having
      to write sensitive data to disk anywhere during the process. This can be
      done by calling `render_preview`, passing in the extra template context
      vars.

    - If the form data is invalid, then the payment details templates needs to
      be re-rendered with the relevant error messages. This can be done by
      calling `render_payment_details`, passing in the form instances to pass
      to the templates.

    The class is deliberately split into fine-grained methods, responsible for
    only one thing.  This is to make it easier to subclass and override just
    one component of functionality.

    All projects will need to subclass and customise this class as no payment
    is taken by default.
    """
    template_name = 'checkout/payment_details.html'
    template_name_preview = 'checkout/preview.html'

    # If preview=True, then we render a preview template that shows all order
    # details ready for submission.
    preview = False

    def post(self, request, *args, **kwargs):
        # Posting to payment-details isn't the right thing to do.  Form
        # submissions should use the preview URL.
        if not self.preview:
            return http.HttpResponseBadRequest()

        # We use a custom parameter to indicate if this is an attempt to place
        # an order (normally from the preview page).  Without this, we assume a
        # payment form is being submitted from the payment details view. In
        # this case, the form needs validating and the order preview shown.
        if request.POST.get('action', '') == 'place_order':
            return self.handle_place_order_submission(request)

        return self.handle_payment_details_submission(request)

    def handle_place_order_submission(self, request):
        """
        Handle a request to place an order.

        This method is normally called after the customer has clicked "place
        order" on the preview page. It's responsible for (re-)validating any
        form information then building the submission dict to pass to the
        `submit` method.

        If forms are submitted on your payment details view, you should
        override this method to ensure they are valid before extracting their
        data into the submission dict and passing it onto `submit`.
        """
        self.checkout_session.confirm_preview()
        return self.checkout()

    def handle_payment_details_submission(self, request):
        """
        Handle a request to submit payment details.

        This method will need to be overridden by projects that require forms
        to be submitted on the payment details view.  The new version of this
        method should validate the submitted form data and:

        - If the form data is valid, show the preview view with the forms
          re-rendered in the page
        - If the form data is invalid, show the payment details view with
          the form errors showing.

        """
        # No form data to validate by default, so we simply render the preview
        # page.  If validating form data and it's invalid, then call the
        # render_payment_details view.
        return self.render_preview(request)

    def render_preview(self, request, **kwargs):
        """
        Show a preview of the order.

        If sensitive data was submitted on the payment details page, you will
        need to pass it back to the view here so it can be stored in hidden
        form inputs.  This avoids ever writing the sensitive data to disk.
        """
        self.preview = True
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    def render_payment_details(self, request, **kwargs):
        """
        Show the payment details page

        This method is useful if the submission from the payment details view
        is invalid and needs to be re-rendered with form errors showing.
        """
        self.preview = False
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

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

    def get_template_names(self):
        return [self.template_name_preview] if self.preview else [
            self.template_name]


# =========
# Thank you
# =========


class ThankYouView(generic.DetailView):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """
    template_name = 'checkout/thank_you.html'
    context_object_name = 'order'

    def get_object(self):
        # We allow superusers to force an order thank-you page for testing
        order = None
        if self.request.user.is_superuser:
            if 'order_number' in self.request.GET:
                order = Order._default_manager.get(
                    number=self.request.GET['order_number'])
            elif 'order_id' in self.request.GET:
                order = Order._default_manager.get(
                    id=self.request.GET['order_id'])

        if not order:
            if 'checkout_order_id' in self.request.session:
                order = Order._default_manager.get(
                    pk=self.request.session['checkout_order_id'])
            else:
                raise http.Http404(_("No order found"))

        return order
