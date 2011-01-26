from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm

from oscar.services import import_module

# Using dynamic app loading
checkout_forms = import_module('checkout.forms', ['DeliveryAddressForm'])

def index(request):
    form = checkout_forms.DeliveryAddressForm()
    return render_to_response('delivery.html', locals(), context_instance=RequestContext(request))


