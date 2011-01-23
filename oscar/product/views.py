from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

# @todo this import needs to be dynamic as we don't necessarily know
# where app the products model is coming from
from oscar.product.models import Item
from oscar.basket.forms import AddToBasketForm

def item(request, product_id, template_file='item.html'):
    """ 
    Single product page
    """
    item = get_object_or_404(Item, pk=product_id)
    form = AddToBasketForm({'product_id': product_id, 'quantity': 1})
    return render_to_response(template_file, locals(), context_instance=RequestContext(request))

def all(request, template_file='browse-all.html'):
    return render_to_response(template_file, locals())
