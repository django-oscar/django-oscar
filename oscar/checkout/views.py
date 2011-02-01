from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.contrib import messages
from django.core.urlresolvers import resolve

from oscar.services import import_module

basket_factory = import_module('basket.factory', ['get_or_create_open_basket', 'get_open_basket', 
                                                  'get_or_create_saved_basket', 'get_saved_basket'])
checkout_forms = import_module('checkout.forms', ['DeliveryAddressForm'])
order_models = import_module('order.models', ['DeliveryAddress', 'Order'])

# @todo move to own module
class OrderTotalCalculator(object):
    
    def __init__(self, request):
        # We store a reference to the request as the total may 
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as delivery method
        # always changes the order total.
        self.request = request
    
    def order_total_incl_tax(self, basket):
        # Default to returning the total including tax - use
        # the request.user object if you want to not charge tax
        # to particular customers.
        return basket.total_incl_tax
    
    def order_total_excl_tax(self, basket):
        return basket.total_excl_tax

class ProgressChecker(object):
    urls_for_steps = ['oscar-checkout-delivery-address',
                      'oscar-checkout-delivery-method',
                      'oscar-checkout-payment',
                      'oscar-checkout-preview']
    
    def are_previous_steps_complete(self, request, url_name):
        """
        Checks whether the previous checkout steps have been completed.
        
        This uses the URL-name and the class-level list of required
        steps.
        """
        complete_steps = request.session.get('checkout_complete_steps', [])
        try:
            current_step_index = self.urls_for_steps.index(url_name)
            last_completed_step_index = len(complete_steps) - 1
            return current_step_index <= last_completed_step_index + 1 
        except ValueError:
            # Can't find current step index - must be manipulation
            return False
        except IndexError:
            # No complete steps - only allowed to be on first page
            return current_step_index == 0
        
    def step_complete(self, request):
        """
        Record a checkout step as complete.
        """
        match = resolve(request.path)
        url_name = match.url_name
        complete_steps = request.session.get('checkout_complete_steps', [])
        if not url_name in complete_steps:
            # Only add name if this is the first time the step 
            # has been completed. 
            complete_steps.append(url_name)
            request.session['checkout_complete_steps'] = complete_steps
            
    def all_steps_complete(self):
        """
        Order has been submitted - clear the completed steps from 
        the session.
        """
        request.session['checkout_complete_steps'] = []

def prev_steps_must_be_complete(view_fn):
    """
    Decorator fn for checking that previous steps of the checkout
    are complete.
    
    The URL-names are stored in the session
    """
    def _view_wrapper(request, *args, **kwargs):
        checker = ProgressChecker()
        # Extract the URL name from the path
        match = resolve(request.path)
        if not checker.are_previous_steps_complete(request, match.url_name):
            messages.error(request, "You must complete the previous steps before this one")
            return HttpResponseRedirect(reverse('oscar-checkout-index'))
        return view_fn(request,*args, **kwargs)
    return _view_wrapper

def mark_step_as_complete(request):
    """ 
    Convenience function for marking a checkout page
    as complete.
    """
    ProgressChecker().step_complete(request)

def index(request):
    """
    Need to check here if the user is ready to start the checkout
    """
    return HttpResponseRedirect(reverse('oscar-checkout-delivery-address'))


def delivery_address(request):
    if request.method == 'POST':
        form = checkout_forms.DeliveryAddressForm(request.POST)
        if form.is_valid():
            # Address data is valid - store in session and redirect to next step.
            clean_data = form.clean()
            if request.user.is_authenticated():
                # Set the user foreign key is user is authenticated
                clean_data['user_id'] = request.user.id 
            request.session['delivery_address'] = clean_data
            
            mark_step_as_complete(request)
            return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
    else:
        if request.session.get('delivery_address', False):
            form = checkout_forms.DeliveryAddressForm(request.session['delivery_address'])
        else:
            form = checkout_forms.DeliveryAddressForm()
    return render(request, 'checkout/delivery_address.html', locals())
    
@prev_steps_must_be_complete    
def delivery_method(request):
    """
    Delivery methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    mark_step_as_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-payment'))

@prev_steps_must_be_complete
def payment(request):
    """
    Payment methods are domain-specific and so need implementing in a s
    subclass of this class.
    """
    mark_step_as_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-preview'))

@prev_steps_must_be_complete
def preview(request):
    """
    Show a preview of the order
    """
    basket = basket_factory.get_open_basket(request)
    
    # Load address data into a blank address model
    addr_data = request.session.get('delivery_address', False)
    if addr_data:
        delivery_addr = order_models.DeliveryAddress(**addr_data)
    
    # Calculate order total
    calc = OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    
    mark_step_as_complete(request)
    return render(request, 'checkout/preview.html', locals())

@prev_steps_must_be_complete
def submit(request):
    """
    Do several things then redirect to the thank-you page
    """
    # Save the delivery address
    addr_data = request.session.get('delivery_address', False)
    if addr_data:
        delivery_addr = order_models.DeliveryAddress(**addr_data)
        delivery_addr.save()
    
    # Save the order model
    calc = OrderTotalCalculator(request)
    basket = basket_factory.get_open_basket(request)
    order_data = {'basket': basket,
                  'total_incl_tax': calc.order_total_incl_tax(basket),
                  'total_excl_tax': calc.order_total_excl_tax(basket),
                  'shipping_incl_tax': 0,
                  'shipping_excl_tax': 0,}
    order = order_models.Order(**order_data).save()
    
    # @todo Save order id in session so thank-you page can load it
    ProgressChecker().all_steps_complete()
    return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))


def thank_you(request):
    return render(request, 'checkout/thank_you.html', locals())