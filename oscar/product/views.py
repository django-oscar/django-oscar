from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from oscar.services import import_module

product_models = import_module('product.models', ['Item'])
basket_forms = import_module('basket.forms', ['AddToBasketForm'])

def item(request, product_id, template_file='item.html'):
    """ 
    Single product page
    """
    item = get_object_or_404(product_models.Item, pk=product_id)
    form = basket_forms.AddToBasketForm({'product_id': product_id, 'quantity': 1})
    return render_to_response(template_file, locals(), context_instance=RequestContext(request))

def all(request, template_file='browse-all.html'):
    return render_to_response(template_file, locals())
