from decimal import Decimal
import logging

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse
from django.core.mail import EmailMessage
from django.views.generic import DetailView, TemplateView, FormView, \
                                 DeleteView, UpdateView, CreateView

from oscar.apps.shipping.methods import FreeShipping
from oscar.core.loading import import_module
import_module('checkout.forms', ['ShippingAddressForm'], locals())
import_module('checkout.calculators', ['OrderTotalCalculator'], locals())
import_module('checkout.utils', ['CheckoutSessionData'], locals())
import_module('checkout.signals', ['pre_payment', 'post_payment'], locals())
import_module('order.models', ['Order', 'ShippingAddress',
                               'CommunicationEvent'], locals())
import_module('order.utils', ['OrderNumberGenerator', 'OrderCreator'], locals())
import_module('address.models', ['UserAddress'], locals())
import_module('address.forms', ['UserAddressForm'], locals())
import_module('shipping.repository', ['Repository'], locals())
import_module('customer.models', ['Email', 'CommunicationEventType'], locals())
import_module('customer.views', ['AccountAuthView'], locals())
import_module('customer.utils', ['Dispatcher'], locals())
import_module('payment.exceptions', ['RedirectRequired', 'UnableToTakePayment', 
                                     'PaymentError'], locals())
import_module('basket.models', ['Basket'], locals())

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class IndexView(AccountAuthView):
    """
    First page of the checkout.  If the user is signed in then we forward
    straight onto the next step.  Otherwise, we provide options to login, register and
    (if the option is enabled) proceed anonymously.
    """
    template_name = 'checkout/gateway.html'
    
    def get_logged_in_redirect(self):
        return reverse('checkout:shipping-address')


class CheckoutSessionMixin(object):
    """
    Mixin to provide common functionality shared between checkout views.
    """   

    def dispatch(self, request, *args, **kwargs):
        self.checkout_session = CheckoutSessionData(request)
        return super(CheckoutSessionMixin, self).dispatch(request, *args, **kwargs)

    def get_shipping_address(self):
        """
        Return the current shipping address for this checkout session.
        
        This could either be a ShippingAddress model which has been
        pre-populated (not saved), or a UserAddress model which will 
        need converting into a ShippingAddress model at submission
        """
        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank address model
            return ShippingAddress(**addr_data)
        addr_id = self.checkout_session.user_address_id()
        if addr_id:
            try:
                return UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # This can happen if you reset all your tables and you still have
                # session data that refers to addresses that no longer exist
                pass
        return None
        
    def get_shipping_method(self, basket=None):
        method = self.checkout_session.shipping_method()
        if method:
            if not basket:
                basket = self.request.basket
            method.set_basket(basket)
        else:
            # We default to using free shipping
            method = FreeShipping()
        return method
    
    def get_order_totals(self, basket=None, shipping_method=None, **kwargs):
        """
        Returns the total for the order with and without tax (as a tuple)
        """
        calc = OrderTotalCalculator(self.request)
        if not basket:
            basket = self.request.basket
        if not shipping_method:
            shipping_method = self.get_shipping_method(basket)
        total_incl_tax = calc.order_total_incl_tax(basket, shipping_method, **kwargs)
        total_excl_tax = calc.order_total_excl_tax(basket, shipping_method, **kwargs)
        return total_incl_tax, total_excl_tax
    
    def get_context_data(self, **kwargs):
        """
        Assign common template variables to the context.
        """
        ctx = super(CheckoutSessionMixin, self).get_context_data(**kwargs)
        ctx['shipping_address'] = self.get_shipping_address()
        
        method = self.get_shipping_method()
        if method:
            ctx['shipping_method'] = method
            ctx['shipping_total_excl_tax'] = method.basket_charge_excl_tax()
            ctx['shipping_total_incl_tax'] = method.basket_charge_incl_tax()
            
        ctx['order_total_incl_tax'], ctx['order_total_excl_tax'] = self.get_order_totals()
        
        return ctx


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
    saved in the session and saved as a model when the order is sucessfully submitted.
    """
    
    template_name = 'checkout/shipping_address.html'
    form_class = ShippingAddressForm
    
    def get_initial(self):
        return self.checkout_session.new_shipping_address_fields()
    
    def get_context_data(self, **kwargs):
        kwargs = super(ShippingAddressView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            # Look up address book data
            kwargs['addresses'] = self.get_available_addresses()
        return kwargs
    
    def get_available_addresses(self):
        return UserAddress._default_manager.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        # Check if a shipping address was selected directly (eg no form was filled in)
        if self.request.user.is_authenticated and 'address_id' in self.request.POST:
            address = UserAddress._default_manager.get(pk=self.request.POST['address_id'])
            if 'action' in self.request.POST and self.request.POST['action'] == 'ship_to':
                # User has selected a previous address to ship to
                self.checkout_session.ship_to_user_address(address)
                return HttpResponseRedirect(self.get_success_url())
            elif 'action' in self.request.POST and self.request.POST['action'] == 'delete':
                address.delete()
                messages.info(self.request, "Address deleted from your address book")
                return HttpResponseRedirect(reverse('checkout:shipping-method'))
            else:
                return HttpResponseBadRequest()
        else:
            return super(ShippingAddressView, self).post(request, *args, **kwargs)
    
    def form_valid(self, form):
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
    template_name = 'checkout/shipping_methods.html';
    
    def get(self, request, *args, **kwargs):
        # Save shipping methods as instance var as we need them both here
        # and when setting the context vars.
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 1:
            # Only one shipping method - set this and redirect onto the next step
            self.checkout_session.use_shipping_method(self._methods[0].code)
            return self.get_success_response()
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
        repo = Repository()
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address.  I haven't come across a scenario that doesn't
        # fit this system.
        return repo.get_shipping_methods(self.request.user, self.request.basket, 
                                         self.get_shipping_address())
    
    def post(self, request, *args, **kwargs):
        method_code = request.POST['method_code']
        # Save the code for the chosen shipping method in the session
        # and continue to the next step.
        self.checkout_session.use_shipping_method(method_code)
        return self.get_success_response()
        
    def get_success_response(self):
        return HttpResponseRedirect(reverse('checkout:payment-method'))


class PaymentMethodView(CheckoutSessionMixin, TemplateView):
    """
    View for a user to choose which payment method(s) they want to use.
    
    This would include setting allocations if payment is to be split
    between multiple sources.
    """
    
    def get(self, request, *args, **kwargs):
        return self.get_success_response()
    
    def get_success_response(self):
        return HttpResponseRedirect(reverse('checkout:preview'))


class OrderPreviewView(CheckoutSessionMixin, TemplateView):
    """
    View a preview of the order before submitting.
    """
    template_name = 'checkout/preview.html'
    
    def get_success_response(self):
        return HttpResponseRedirect(reverse('checkout:payment-details'))


class OrderPlacementMixin(CheckoutSessionMixin):
    """
    Mixin for providing functionality for placing orders.
    """
    # Any payment sources should be added to this list as part of the
    # _handle_payment method.  If the order is placed successfully, then
    # they will be persisted.
    _payment_sources = None
    communication_type_code = 'ORDER_PLACED' 
    
    def handle_order_placement(self, order_number, basket, total_incl_tax, total_excl_tax, **kwargs): 
        """
        Place the order into the database and return the appropriate HTTP response
        
        We deliberately pass the basket in here as the one tied to the request
        isn't necessarily the correct one to use in placing the order.  This can
        happen when a basket gets frozen.
        """   
        # Write out all order and payment models
        order = self.place_order(order_number, basket, total_incl_tax, total_excl_tax, **kwargs)
        basket.set_as_submitted()
        return self.handle_successful_order(order)
        
    def add_payment_source(self, source):
        if self._payment_sources is None:
            self._payment_sources = []
        self._payment_sources.append(source)  
        
    def handle_successful_order(self, order):  
        """
        Handle the various steps required after an order has been successfully placed.
        """  
        # Send confirmation message (normally an email)
        self.send_confirmation_message(order)
        
        # Flush all session data
        self.checkout_session.flush()
        
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id
        return HttpResponseRedirect(reverse('checkout:thank-you'))
    
    def place_order(self, order_number, basket, total_incl_tax, total_excl_tax, **kwargs):
        """
        Writes the order out to the DB including the payment models
        """
        shipping_address = self.create_shipping_address()
        shipping_method = self.get_shipping_method(basket)
        billing_address = self.create_billing_address(shipping_address)
        if 'status' not in kwargs:
            status = self.get_initial_order_status(basket)
        else:
            status = kwargs.pop('status')
        order = OrderCreator().place_order(self.request.user, 
                                         basket, 
                                         shipping_address, 
                                         shipping_method, 
                                         billing_address,
                                         total_incl_tax,
                                         total_excl_tax,
                                         order_number,
                                         status,
                                         **kwargs)
        self.save_payment_details(order)
        return order
    
    def create_shipping_address(self):
        """
        Create and returns the shipping address for the current order.
        
        If the shipping address was entered manually, then we simply
        write out a ShippingAddress model with the appropriate form data.  If
        the user is authenticated, then we create a UserAddress from this data
        too so it can be re-used in the future. 
        
        If the shipping address was selected from the user's address book,
        then we convert the UserAddress to a ShippingAddress.
        """
        addr_data = self.checkout_session.new_shipping_address_fields()
        addr_id = self.checkout_session.user_address_id()
        if addr_data:
            addr = self.create_shipping_address_from_form_fields(addr_data)
            self.create_user_address(addr_data)
        elif addr_id:
            addr = self.create_shipping_address_from_user_address(addr_id)
        else:
            raise AttributeError("No shipping address data found")
        return addr
    
    def create_shipping_address_from_form_fields(self, addr_data):
        """Creates a shipping address model from the saved form fields"""
        shipping_addr = ShippingAddress(**addr_data)
        shipping_addr.save() 
        return shipping_addr
    
    def create_user_address(self, addr_data):
        """
        For signed-in users, we create a user address model which will go 
        into their address book.
        """
        if self.request.user.is_authenticated():
            addr_data['user_id'] = self.request.user.id
            user_addr = UserAddress(**addr_data)
            # Check that this address isn't already in the db as we don't want
            # to fill up the customer address book with duplicate addresses
            try:
                UserAddress._default_manager.get(hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                user_addr.save()
    
    def create_shipping_address_from_user_address(self, addr_id):
        """Creates a shipping address from a user address"""
        address = UserAddress._default_manager.get(pk=addr_id)
        # Increment the number of orders to help determine popularity of orders 
        address.num_orders += 1
        address.save()
        
        shipping_addr = ShippingAddress()
        address.populate_alternative_model(shipping_addr)
        shipping_addr.save()
        return shipping_addr
    
    def create_billing_address(self, shipping_address=None):
        """
        Saves any relevant billing data (eg a billing address).
        """
        return None

    def save_payment_details(self, order):
        """
        Saves all payment-related details. This could include a billing 
        address, payment sources and any order payment events.
        """
        self.save_payment_events(order)
        self.save_payment_sources(order)
    
    def save_payment_events(self, order):
        """
        Saves any relevant payment events for this order
        """
        pass

    def save_payment_sources(self, order):
        """
        Saves any payment sources used in this order.
        
        When the payment sources are created, the order model does not exist and 
        so they need to have it set before saving.
        """
        if not self._payment_sources:
            return
        for source in self._payment_sources:
            source.order = order
            source.save()
    
    def get_initial_order_status(self, basket):
        return None
        
    def get_submitted_basket(self):
        basket_id = self.checkout_session.get_submitted_basket_id()
        return Basket._default_manager.get(pk=basket_id)
    
    def restore_frozen_basket(self):
        """
        Restores a frozen basket as the sole OPEN basket.  Note that this also merges
        in any new products that have been added to a basket that has been created while payment.
        """
        try:
            fzn_basket = self.get_submitted_basket()
        except Basket.DoesNotExist:
            # Strange place.  The previous basket stored in the session does
            # not exist.
            pass
        else:
            fzn_basket.thaw()
            if self.request.basket.id != fzn_basket.id:
                fzn_basket.merge(self.request.basket)
                self.request.basket = fzn_basket

    def send_confirmation_message(self, order):
        code = self.communication_type_code
        ctx = {'order': order,
               'lines': order.lines.all(),}
        try:
            event_type = CommunicationEventType.objects.get(code=code)
        except CommunicationEventType.DoesNotExist:
            # No event in database, attempt to find templates for this type
            messages = CommunicationEventType.objects.get_and_render(code, ctx)
            event_type = None
        else:
            # Create order event
            CommunicationEvent._default_manager.create(order=order, type=event_type)
            messages = event_type.get_messages(ctx)

        if messages and messages['body']:      
            logger.info("Order #%s - sending %s messages", order.number, code)  
            dispatcher = Dispatcher(logger)
            dispatcher.dispatch_order_messages(order, messages, event_type)
        else:
            logger.warning("Order #%s - no %s communication event type", order.number, code)


class PaymentDetailsView(OrderPlacementMixin, TemplateView):
    """
    For taking the details of payment and creating the order
    
    The class is deliberately split into fine-grained methods, responsible for only one
    thing.  This is to make it easier to subclass and override just one component of
    functionality.
    
    Almost all projects will need to subclass and customise this class.
    """
    
    def post(self, request, *args, **kwargs):
        """
        This method is designed to be overridden by subclasses which will
        validate the forms from the payment details page.  If the forms are valid
        then the method can call submit()."""
        return self.submit(request.basket, **kwargs)
    
    def submit(self, basket, **kwargs):
        """
        Submit a basket for order placement.
        
        The process runs as follows:
         * Generate an order number
         * Freeze the basket so it cannot be modified any more.
         * Attempt to take payment for the order
           - If payment is successful, place the order
           - If a redirect is required (eg PayPal, 3DSecure), redirect
           - If payment is unsuccessful, show an appropriate error message
        """
        # First check that basket isn't empty
        if basket.is_empty:
            messages.error(self.request, _("This order cannot be submitted as the basket is empty"))
            return HttpResponseRedirect(self.request.META['HTTP_REFERER'])

        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been 
        # created).  We also save it in the session for multi-stage
        # checkouts (eg where we redirect to a 3rd party site and place
        # the order on a different request).
        order_number = self.generate_order_number(basket)
        logger.info("Order #%s: beginning submission process for basket %d", order_number, basket.id)
        
        self.freeze_basket(basket)
        self.checkout_session.set_submitted_basket(basket)
        
        # Handle payment.  Any payment problems should be handled by the 
        # handle_payment method raise an exception, which should be caught
        # within handle_POST and the appropriate forms redisplayed.
        try:
            pre_payment.send_robust(sender=self, view=self)
            total_incl_tax, total_excl_tax = self.get_order_totals(basket)
            self.handle_payment(order_number, total_incl_tax, **kwargs)
            post_payment.send_robust(sender=self, view=self)
        except RedirectRequired, e:
            # Redirect required (eg PayPal, 3DS)
            logger.info("Order #%s: redirecting to %s", order_number, e.url)
            return HttpResponseRedirect(e.url)
        except UnableToTakePayment, e:
            # Something went wrong with payment, need to show
            # error to the user.  This type of exception is supposed
            # to set a friendly error message.
            msg = unicode(e)
            logger.warning("Order #%s: unable to take payment (%s) - restoring basket", order_number, msg)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error=msg))
        except PaymentError, e:
            # Something went wrong which wasn't anticipated.
            msg = unicode(e)
            logger.error("Order #%s: payment error (%s)", order_number, msg)
            self.restore_frozen_basket()
            return self.render_to_response(self.get_context_data(error="A problem occurred processing payment."))
        else:
            # If all is ok with payment, place order
            logger.info("Order #%s: payment successful, placing order", order_number)
            return self.handle_order_placement(order_number, basket, total_incl_tax, total_excl_tax, **kwargs)
    
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
        Handle any payment processing.  
        
        This method is designed to be overridden within your project.  The
        default is to do nothing.
        """
        pass


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
