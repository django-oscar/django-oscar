from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

from oscar.services import import_module

# Using dynamic loading
basket_models = import_module('basket.models', ['Basket', 'Line'])
basket_forms = import_module('basket.forms', ['AddToBasketForm'])
basket_factory = import_module('basket.factory', ['get_or_create_basket', 'get_basket'])
product_models = import_module('product.models', ['Item'])


def index(request, template_file='basket/summary.html'):
    """ 
    Pages should POST to this view to add an item to someone's basket
    """
    if request.method == 'POST': 
        form = basket_forms.AddToBasketForm(request.POST)
        if not form.is_valid():
            # @todo Handle form errors in the add-to-basket form
            return HttpResponseBadRequest("Unable to add your item to the basket - submission not valid")
        try:
            # We create the response object early as the basket creation
            # may need to set a cookie on it
            response = HttpResponseRedirect(reverse('oscar-basket'))
            product = product_models.Item.objects.get(pk=form.cleaned_data['product_id'])
            basket = basket_factory.get_or_create_basket(request, response)
            basket.add_product(product, form.cleaned_data['quantity'])
        except product_models.Item.DoesNotExist, e:
            response = HttpResponseBadRequest("Unable to find the requested item to add to your basket")
        except basket_models.Basket.DoesNotExist, e:
            response = HttpResponseBadRequest("Unable to find your basket") 
    else:
        # Display the visitor's basket
        basket = basket_factory.get_basket(request)
        if not basket:
            basket = basket_models.Basket()
            
        response = render_to_response(template_file, locals(), context_instance=RequestContext(request))
    return response

def line(request, line_reference):
    """
    For requests that alter a basket line.
    
    This can take a few different "action" names such as increment-quantity,
    decrement-quantity, set-quantity and delete.
    """
    response = HttpResponseRedirect(reverse('oscar-basket'))
    if request.method == 'POST': 
        try:
            basket = basket_factory.get_basket(request)
            line = basket.lines.get(line_reference=line_reference)
            if request.POST.has_key('increment-quantity'):
                line.quantity += int(request.POST['increment-quantity'])
            elif request.POST.has_key('decrement-quantity'):
                line.quantity -= int(request.POST['decrement-quantity'])
            elif request.POST.has_key('set-quantity'):
                line.quantity = int(request.POST['set-quantity'])
            elif request.POST.has_key('delete'):
                line.quantity = 0
            line.save()    
        except basket_models.Line.DoesNotExist:
            response = Http404("Unable to find a line with reference %s in your basket" % line_reference)     
        except basket_models.Basket.DoesNotExist:
            response = HttpResponseBadRequest("You don't have a basket to adjust the lines of") 
    return response
