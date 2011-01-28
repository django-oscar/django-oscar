from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, render
from django.core.urlresolvers import reverse
from django.contrib import messages

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
        response = HttpResponseRedirect(reverse('oscar-basket'))
        
        # Load basket to act on
        try:
            basket = basket_factory.get_or_create_basket(request, response)
        except basket_models.Basket.DoesNotExist, e:
            # Suspicous request as the user's basket could not be found
            return Http404("Unable to find your basket") 
        
        # All updates to a basket must specify the action to take
        if not request.POST.has_key('action'):
            return Http404("You must specify a valid action") 
        
        if request.POST['action'] == 'flush':
            basket.flush()
            messages.info(request, "Your basket has been emptied")
        elif request.POST['action'] == 'add':
            form = basket_forms.AddToBasketForm(request.POST)
            if not form.is_valid():
                # @todo Handle form errors in the add-to-basket form
                return HttpResponseBadRequest("Unable to add your item to the basket - submission not valid")
            product = get_object_or_404(product_models.Item.objects, pk=form.cleaned_data['product_id'])
            basket.add_product(product, form.cleaned_data['quantity'])
            messages.info(request, "'%s' (quantity %d) has been added to your basket" %
                          (product.get_title(), form.cleaned_data['quantity']))
    else:
        # Display the visitor's basket
        basket = basket_factory.get_basket(request)
        if not basket:
            basket = basket_models.Basket()
            
        response = render(request, template_file, locals(), context_instance=RequestContext(request))
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
                messages.info(request, "The quantity of '%s' has been increased by %d" %
                              (line.product, int(request.POST['increment-quantity'])))
            elif request.POST.has_key('decrement-quantity'):
                line.quantity -= int(request.POST['decrement-quantity'])
                messages.info(request, "The quantity of '%s' has been decreased by %d" % 
                              (line.product, int(request.POST['decrement-quantity'])))
            elif request.POST.has_key('set-quantity') and request.POST['set-quantity'].isdigit():
                if int(request.POST['set-quantity']) >= 0:
                    line.quantity = int(request.POST['set-quantity'])
                    messages.info(request, "The quantity of '%s' has been set to %d" %
                              (line.product, int(request.POST['set-quantity'])))
            elif request.POST.has_key('delete'):
                line.quantity = 0
                messages.info(request, "'%s' has been removed from your basket" % line.product)
            line.save()    
        except basket_models.Line.DoesNotExist:
            response = Http404("Unable to find a line with reference %s in your basket" % line_reference)     
        except basket_models.Basket.DoesNotExist:
            response = HttpResponseBadRequest("You don't have a basket to adjust the lines of") 
    return response
