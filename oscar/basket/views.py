from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, render
from django.core.urlresolvers import reverse
from django.contrib import messages

from oscar.services import import_module

# Using dynamic loading
basket_models = import_module('basket.models', ['Basket', 'Line', 'InvalidBasketLineError'])
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


class LineView(object):
    
    def __call__(self, request, line_reference):
        self.request = request
        
        # Whatever happens, the response is a redirect back to the 
        # basket summary page
        response = HttpResponseRedirect(reverse('oscar-basket'))
        
        # All modifications to a line must come via a POST request 
        # which has an 'action' parameter
        if request.method == 'POST' or 'action' in request.POST:
            try:
                basket = basket_factory.get_basket(request)
                line = basket.lines.get(line_reference=line_reference)
                
                # We look for a method of the form do_... which can handle
                # the requested action
                callback = getattr(self, "do_%s" % request.POST['action'].lower())(line)
                
            except basket_models.Basket.DoesNotExist:
                messages.error(request, "You don't have a basket to adjust the lines of")
            except basket_models.Line.DoesNotExist:
                messages.error(request, "Unable to find a line with reference %s in your basket" % line_reference)
            except AttributeError:
                messages.error(request, "Invalid basket action")
            except basket_models.InvalidBasketLineError, e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Invalid request")
        return response
        
    def _get_quantity(self):
        if 'quantity' in self.request.POST:
            return int(self.request.POST['quantity'])
        return 0        
            
    def do_increment_quantity(self, line):
        q = self._get_quantity()
        line.quantity += q
        line.save()    
        msg = "The quantity of '%s' has been increased by %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_decrement_quantity(self, line):
        q = self._get_quantity()
        line.quantity -= q
        line.save()    
        msg = "The quantity of '%s' has been decreased by %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_set_quantity(self, line):
        q = self._get_quantity()
        line.quantity = q
        line.save()    
        msg = "The quantity of '%s' has been set to %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_delete(self, line):
        line.delete()
        msg = "'%s' has been removed from your basket" % line.product
        messages.warn(self.request, msg)