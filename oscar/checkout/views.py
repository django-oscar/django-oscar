from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm

from oscar.services import import_module

# Using dynamic app loading
checkout_forms = import_module('checkout.forms', ['DeliveryAddressForm'])


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
    return HttpResponseRedirect(reverse('oscar-checkout-payment'))


def payment(request):
    return HttpResponseRedirect(reverse('oscar-checkout-preview'))


def preview(request):
    return render(request, 'checkout/preview.html', locals())