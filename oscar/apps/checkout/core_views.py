from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib import messages
from django.core.urlresolvers import reverse

from oscar.core.loading import import_module
basket_factory = import_module('basket.factory', ['BasketFactory'])
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
order_models = import_module('order.models', ['Order', 'ShippingAddress'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker', 'CheckoutSessionData'])
address_models = import_module('address.models', ['UserAddress'])

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
        method = self.co_data.shipping_method()
        if method:
            method.set_basket(self.basket)
        
        self.context = {'basket': self.basket,
                        'order_total': self.get_order_total(method),
                        'shipping_addr': self.get_shipping_address()}
        self.set_shipping_context(method)
        self.set_payment_context()
        
        if request.method == 'POST':
            response = self.handle_POST()
        elif request.method == 'GET':
            response = self.handle_GET()
        else:
            response = HttpResponseBadRequest()
        return response
    
    def set_shipping_context(self, method):
        if method:
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
    
    def get_order_total(self, shipping_method):
        calc = checkout_calculators.OrderTotalCalculator(self.request)
        return calc.order_total_incl_tax(self.basket, shipping_method)
    
    def get_shipping_address(self):
        # Load address data into a blank address model
        addr_data = self.co_data.new_address_fields()
        if addr_data:
            return order_models.ShippingAddress(**addr_data)
        addr_id = self.co_data.user_address_id()
        if addr_id:
            try:
                return address_models.UserAddress._default_manager.get(pk=addr_id)
            except address_models.UserAddress.DoesNotExist:
                # This can happen if you reset all your tables and you still have
                # session data that refers to addresses that no longer exist
                pass
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
