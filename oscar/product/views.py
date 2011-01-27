from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from oscar.services import import_module

product_models = import_module('product.models', ['Item'])
basket_forms = import_module('basket.forms', ['AddToBasketForm'])

def item(request, product_id, template_file='product/item.html'):
    """ 
    Single product page
    """
    item = get_object_or_404(product_models.Item, pk=product_id)
    form = basket_forms.AddToBasketForm({'product_id': product_id, 'quantity': 1, 'action': 'add'})
    return render_to_response(template_file, locals(), context_instance=RequestContext(request))

def all(request, template_file='product/browse-all.html', results_per_page=20):
    product_list = product_models.Item.browsable.all()
    paginator = Paginator(product_list, results_per_page)
    
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    # If page request (9999) is out of range, deliver last page of results.
    try:
        products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)
    
    return render_to_response(template_file, locals())
