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
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker'])
order_models = import_module('order.models', ['DeliveryAddress', 'Order'])
address_models = import_module('address.models', ['UserAddress'])

def prev_steps_must_be_complete(view_fn):
    """
    Decorator fn for checking that previous steps of the checkout
    are complete.
    
    The completed steps (identified by URL-names) are stored in the session.
    If this fails, then we redirect to the next uncompleted step.
    """
    def _view_wrapper(request, *args, **kwargs):
        checker = checkout_utils.ProgressChecker()
        if not checker.are_previous_steps_complete(request):
            messages.error(request, "You must complete this step of the checkout first")
            url_name = checker.get_next_step(request)
            return HttpResponseRedirect(reverse(url_name))
        return view_fn(request,*args, **kwargs)
    return _view_wrapper


def mark_step_as_complete(request):
    """ 
    Convenience function for marking a checkout page
    as complete.
    """
    checkout_utils.ProgressChecker().step_complete(request)


def index(request):
    """
    Need to check here if the user is ready to start the checkout
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('oscar-checkout-delivery-address'))
    return render(request, 'checkout/gateway.html', locals())


def delivery_address(request):
    if request.method == 'POST':
        form = checkout_forms.DeliveryAddressForm(request.POST)
        if form.is_valid():
            # Address data is valid - store in session and redirect to next step.
            clean_data = form.clean()
            request.session['delivery_address'] = clean_data
            
            # Also record whether this address should be the default delivery address
            if 'save_as_default' in request.POST and request.POST['save_as_default'] == 'on':
                request.session['save_as_default'] = True
            
            mark_step_as_complete(request)
            return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
    else:
        if request.session.get('delivery_address', False):
            form = checkout_forms.DeliveryAddressForm(request.session['delivery_address'])
        else:
            form = checkout_forms.DeliveryAddressForm()
    
    # Add in extra template bindings
    basket = basket_factory.get_open_basket(request)
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    delivery_total_excl_tax = 0
    delivery_total_incl_tax = 0
    
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
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    
    mark_step_as_complete(request)
    return render(request, 'checkout/preview.html', locals())

@prev_steps_must_be_complete
def submit(request):
    """
    Do several things then redirect to the thank-you page
    """
    # Save the address data
    addr_data = request.session.get('delivery_address', False)
    if addr_data:
        # Delivery address
        delivery_addr = order_models.DeliveryAddress(**addr_data)
        delivery_addr.save()
        
        # User address
        if request.user.is_authenticated():
            addr_data['user_id'] = request.user.id
            user_addr = address_models.UserAddress(**addr_data)
            is_default = request.session.get('save_as_default', False)
            if is_default:
                user_addr.is_primary = True 
            user_addr.save()
    
    # Save the order model
    calc = checkout_calculators.OrderTotalCalculator(request)
    basket = basket_factory.get_open_basket(request)
    order_data = {'basket': basket,
                  'total_incl_tax': calc.order_total_incl_tax(basket),
                  'total_excl_tax': calc.order_total_excl_tax(basket),
                  'shipping_incl_tax': 0,
                  'shipping_excl_tax': 0,}
    order = order_models.Order(**order_data).save()
    
    # @todo set basket as submitted
    
    # @todo Save order id in session so thank-you page can load it
    checkout_utils.ProgressChecker().all_steps_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))


def thank_you(request):
    return render(request, 'checkout/thank_you.html', locals())