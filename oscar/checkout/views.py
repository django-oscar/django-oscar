from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.core.exceptions import ObjectDoesNotExist

from oscar.views import ModelView
from oscar.services import import_module

basket_factory = import_module('basket.factory', ['BasketFactory'])
checkout_forms = import_module('checkout.forms', ['ShippingAddressForm'])
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker', 'CheckoutSessionData'])
checkout_signals = import_module('checkout.signals', ['order_placed', 'pre_payment', 'post_payment'])
order_models = import_module('order.models', ['Order', 'ShippingAddress'])
order_utils = import_module('order.utils', ['OrderCreator'])
address_models = import_module('address.models', ['UserAddress'])
shipping_repository = import_module('shipping.repository', ['Repository'])

def prev_steps_must_be_complete(view_fn):
    u"""
    Decorator fn for checking that previous steps of the checkout
    are complete.
    
    The completed steps (identified by URL-names) are stored in the session.
    If this fails, then we redirect to the next uncompleted step.
    """
    def _view_wrapper(self, request, *args, **kwargs):
        checker = checkout_utils.ProgressChecker()
        if not checker.are_previous_steps_complete(request):
            messages.error(request, "You must complete this step of the checkout first")
            url_name = checker.get_next_step(request)
            return HttpResponseRedirect(reverse(url_name))
        return view_fn(self, request, *args, **kwargs)
    return _view_wrapper

def basket_required(view_fn):
    def _view_wrapper(self, request, *args, **kwargs):
        basket = basket_factory.BasketFactory().get_open_basket(request)
        if not basket:
            messages.error(request, "You must add some products to your basket before checking out")
            return HttpResponseRedirect(reverse('oscar-basket'))
        return view_fn(self, request, *args, **kwargs)
    return _view_wrapper

def mark_step_as_complete(request):
    u""" 
    Convenience function for marking a checkout page
    as complete.
    """
    checkout_utils.ProgressChecker().step_complete(request)
    
def get_next_step(request):
    return checkout_utils.ProgressChecker().get_next_step(request)


class CheckoutView(object):
    u"""
    Top-level superclass for all checkout view classes
    """
    
    def __init__(self, template_file=None):
        if template_file:
            self.template_file = template_file
        
    @basket_required
    @prev_steps_must_be_complete
    def __call__(self, request):
        u"""
        We forward request handling to the appropriate method
        based on the HTTP method.
        """
        
        # Set up the instance variables that are needed to place an order
        self.request = request
        self.co_data = checkout_utils.CheckoutSessionData(request)
        self.basket = basket_factory.BasketFactory().get_open_basket(self.request)
        
        # Set up template context that is available to every view
        self.context = {'basket': self.basket,
                        'order_total': self.get_order_total(),
                        'shipping_addr': self.get_shipping_address()}
        self.set_shipping_context()
        self.set_payment_context()
        
        if request.method == 'POST':
            response = self.handle_POST()
        elif request.method == 'GET':
            response = self.handle_GET()
        else:
            response = HttpResponseBadRequest()
        return response
    
    def set_shipping_context(self):
        method = self.co_data.shipping_method()
        if method:
            method.set_basket(self.basket)
            self.context['method'] = method
            self.context['shipping_total_excl_tax'] = method.basket_charge_excl_tax()
            self.context['shipping_total_incl_tax'] = method.basket_charge_incl_tax()
            
    def set_payment_context(self):
        method = self.co_data.payment_method()
        if method:
            self.context['payment_method'] = method
    
    def handle_GET(self):
        u"""
        Default behaviour is to set step as complete and redirect
        to the next step.
        """ 
        return self.get_success_response()
    
    def get_order_total(self):
        calc = checkout_calculators.OrderTotalCalculator(self.request)
        return calc.order_total_incl_tax(self.basket)
    
    def get_shipping_address(self):
        # Load address data into a blank address model
        addr_data = self.co_data.new_address_fields()
        if addr_data:
            return order_models.ShippingAddress(**addr_data)
        addr_id = self.co_data.user_address_id()
        if addr_id:
            return address_models.UserAddress.objects.get(pk=addr_id)
        return None
    
    def get_success_response(self):
        u"""
        Returns the appropriate redirect response if a checkout
        step has been successfully passed.
        """
        mark_step_as_complete(self.request)
        return HttpResponseRedirect(reverse(get_next_step(self.request)))
    
    def handle_POST(self):
        pass


class IndexView(object):
    template_file = 'checkout/gateway.html'
    
    def __call__(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('oscar-checkout-shipping-address'))
        return render(request, self.template_file, locals())    


class ShippingAddressView(CheckoutView):
    template_file = 'checkout/shipping_address.html'
    
    def handle_POST(self):
        if self.request.user.is_authenticated and 'address_id' in self.request.POST:
            address = address_models.UserAddress.objects.get(pk=self.request.POST['address_id'])
            if 'action' in self.request.POST and self.request.POST['action'] == 'ship_to':
                # User has selected a previous address to ship to
                self.co_data.ship_to_user_address(address)
                return self.get_success_response()
            elif 'action' in self.request.POST and self.request.POST['action'] == 'delete':
                address.delete()
                messages.info(self.request, "Address deleted from your address book")
                return HttpResponseRedirect(reverse('oscar-checkout-shipping-method'))
            else:
                return HttpResponseBadRequest()
        else:
            form = checkout_forms.ShippingAddressForm(self.request.POST)
            if form.is_valid():
                # Address data is valid - store in session and redirect to next step.
                self.co_data.ship_to_new_address(form.clean())
                return self.get_success_response()
            return self.handle_GET(form)
        
    def handle_GET(self, form=None):
        if not form:
            addr_fields = self.co_data.new_address_fields()
            if addr_fields:
                form = checkout_forms.ShippingAddressForm(addr_fields)
            else:
                form = checkout_forms.ShippingAddressForm()
        self.context['form'] = form
    
        # Look up address book data
        if self.request.user.is_authenticated():
            self.context['addresses'] = address_models.UserAddress.objects.filter(user=self.request.user)
        
        return render(self.request, self.template_file, self.context)
    
    
class ShippingMethodView(CheckoutView):
    u"""
    Shipping methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    template_file = 'checkout/shipping_methods.html';
    
    def handle_GET(self):
        methods = self.get_available_shipping_methods()
        if len(methods) == 1:
            # Only one method - set this and redirect onto the next step
            self.co_data.use_shipping_method(methods[0].code)
            return self.get_success_response()
        
        self.context['methods'] = methods
        return render(self.request, self.template_file, self.context)
    
    def get_available_shipping_methods(self):
        u"""
        Returns all applicable shipping method objects
        for a given basket.
        """ 
        repo = shipping_repository.Repository()
        return repo.get_shipping_methods(self.request.user, self.basket, self.get_shipping_address())
    
    def handle_POST(self):
        method_code = self.request.POST['method_code']
        self.co_data.use_shipping_method(method_code)
        return self.get_success_response()
        

class PaymentMethodView(CheckoutView):
    u"""
    View for a user to choose which payment method(s) they want to use.
    
    This would include setting allocations if payment is to be split
    between multiple sources.
    """
    pass


class OrderPreviewView(CheckoutView):
    u"""View a preview of the order before submitting."""
    
    template_file = 'checkout/preview.html'
    
    def handle_GET(self):
        mark_step_as_complete(self.request)
        return render(self.request, self.template_file, self.context)


class PaymentDetailsView(CheckoutView):
    u"""
    For taking the details of payment.
    
    This has to be the final step before submit as we don't want to store
    payment details in the session.
    """
    pass


class SubmitView(CheckoutView):
    u"""
    Class for submitting an order.
    
    The class is deliberately split into fine-grained method, responsible for only one
    thing.  This is to make it easier to subclass and override just one component of
    functionality.
    
    Note that the order models support shipping to multiple addresses but the default
    implementation assumes only one.  To change this, override the _get_shipping_address_for_line
    method.
    """
    
    def handle_GET(self):
        return self.handle_POST()
    
    def handle_POST(self):
        
        checkout_signals.pre_payment.send_robust(sender=self, view=self)
        self._handle_payment(self.basket)
        checkout_signals.post_payment.send_robust(sender=self, view=self)
        order = self._place_order(self.basket)
        self._reset_checkout()
        checkout_signals.order_placed.send_robust(sender=self, order=order)
        
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id
        return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))
    
    def _handle_payment(self, basket):
        u"""Handle any payment processing"""
        pass
    
    def _reset_checkout(self):
        u"""Reset any checkout session state"""
        self.co_data.flush()
        checkout_utils.ProgressChecker().all_steps_complete(self.request)
    
    def _place_order(self, basket):
        u"""Writes the order out to the DB"""
        calc = checkout_calculators.OrderTotalCalculator(self.request)
        shipping_address = self._get_shipping_address()
        shipping_method = self._get_shipping_method(basket)
        order_creator = order_utils.OrderCreator(calc)
        return order_creator.place_order(self.request.user, basket, shipping_address, shipping_method)
    
    def _get_shipping_method(self, basket):
        u"""Returns the shipping method object"""
        method = self.co_data.shipping_method()
        method.set_basket(basket)
        return method
    
    def _get_shipping_address(self):
        u"""Returns the shipping address"""
        addr_data = self.co_data.new_address_fields()
        addr_id = self.co_data.user_address_id()
        if addr_data:
            addr = self._create_shipping_address_from_form_fields(addr_data)
            self._create_user_address(addr_data)
        elif addr_id:
            addr = self._create_shipping_address_from_user_address(addr_id)
        else:
            raise AttributeError("No shipping address data found")
        return addr
    
    def _create_shipping_address_from_form_fields(self, addr_data):
        u"""Creates a shipping address model from the saved form fields"""
        shipping_addr = order_models.ShippingAddress(**addr_data)
        shipping_addr.save() 
        return shipping_addr
    
    def _create_user_address(self, addr_data):
        u"""
        For signed-in users, we create a user address model which will go 
        into their address book.
        """
        if self.request.user.is_authenticated():
            addr_data['user_id'] = self.request.user.id
            user_addr = address_models.UserAddress(**addr_data)
            # Check that this address isn't already in the db as we don't want
            # to fill up the customer address book with duplicate addresses
            try:
                duplicate_addr = address_models.UserAddress.objects.get(hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                user_addr.save()
    
    def _create_shipping_address_from_user_address(self, addr_id):
        u"""Creates a shipping address from a user address"""
        address = address_models.UserAddress.objects.get(pk=addr_id)
        # Increment the number of orders to help determine popularity of orders 
        address.num_orders += 1
        address.save()
        
        shipping_addr = order_models.ShippingAddress()
        address.populate_alternative_model(shipping_addr)
        shipping_addr.save()
        return shipping_addr


class ThankYouView(object):
    
    def __call__(self, request):
        try:
            order = order_models.Order.objects.get(pk=request.session['checkout_order_id'])
            
            # Remove order number from session 
            del request.session['checkout_order_id']
        except KeyError, ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('oscar-checkout-index'))
        return render(request, 'checkout/thank_you.html', locals())
