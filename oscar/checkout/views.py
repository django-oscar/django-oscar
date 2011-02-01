from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm

from oscar.services import import_module

basket_factory = import_module('basket.factory', ['get_or_create_open_basket', 'get_open_basket', 
                                                  'get_or_create_saved_basket', 'get_saved_basket'])
checkout_forms = import_module('checkout.forms', ['DeliveryAddressForm'])
order_models = import_module('order.models', ['DeliveryAddress'])

class OrderTotalCalculator(object):
    
    def __init__(self, request):
        # We store a reference to the request as the total may 
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as delivery method
        # always changes the order total.
        self.request = request
    
    def order_total(self, basket):
        # Default to returning the total including tax - use
        # the request.user object if you want to not charge tax
        # to particular customers.
        return basket.total_incl_tax


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
            request.session['delivery_address'] = clean_data
            return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
    else:
        if request.session.get('delivery_address', False):
            form = checkout_forms.DeliveryAddressForm(request.session['delivery_address'])
        else:
            form = checkout_forms.DeliveryAddressForm()
    return render(request, 'checkout/delivery_address.html', locals())
    
    
def delivery_method(request):
    """
    Delivery methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    return HttpResponseRedirect(reverse('oscar-checkout-payment'))


def payment(request):
    """
    Payment methods are domain-specific and so need implementing in a s
    subclass of this class.
    """
    return HttpResponseRedirect(reverse('oscar-checkout-preview'))


def preview(request):
    """
    Show a preview of the order
    """
    basket = basket_factory.get_open_basket(request)
    
    # Load address data into a blank address model
    addr_data = request.session.get('delivery_address')
    delivery_addr = order_models.DeliveryAddress(**addr_data)
    
    # Calculate order total
    calc = OrderTotalCalculator(request)
    order_total = calc.order_total(basket)
    
    return render(request, 'checkout/preview.html', locals())


def submit(request):
    """
    Do several things then redirect to the thank-you page
    """
    return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))


def thank_you(request):
    return render(request, 'checkout/thank_you.html', locals())