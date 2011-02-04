from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, render
from django.core.urlresolvers import reverse
from django.contrib import messages

from oscar.views import ModelView
from oscar.services import import_module

basket_models = import_module('basket.models', ['Basket', 'Line', 'InvalidBasketLineError'])
basket_forms = import_module('basket.forms', ['FormFactory'])
basket_factory = import_module('basket.factory', ['get_or_create_open_basket', 'get_open_basket', 
                                                  'get_or_create_saved_basket', 'get_saved_basket'])
product_models = import_module('product.models', ['Item'])
    
        
class BasketView(ModelView):
    template_file = 'basket/summary.html'
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
    
    def get_model(self):
        return basket_factory.get_or_create_open_basket(self.request, self.response)
    
    def handle_GET(self, basket):
        basket = basket_factory.get_open_basket(self.request)
        saved_basket = basket_factory.get_saved_basket(self.request)
        if not basket:
            basket = basket_models.Basket()
        self.response = render(self.request, self.template_file, locals())
        
    def handle_POST(self, basket):
        try:
            super(BasketView, self).handle_POST(basket)
        except basket_models.Basket.DoesNotExist:
            messages.error(self.request, "Unable to find your basket")
        except basket_models.InvalidBasketLineError, e:
            messages.error(self.request, str(e))
            
    def do_flush(self, basket):
        basket.flush()
        messages.info(self.request, "Your basket has been emptied")
        
    def do_add(self, basket):
        item = get_object_or_404(product_models.Item.objects, pk=self.request.POST['product_id'])
        factory = basket_forms.FormFactory()
        form = factory.create(item, self.request.POST)
        if not form.is_valid():
            self.response = HttpResponseRedirect(item.get_absolute_url())
            messages.error(self.request, "Unable to add your item to the basket - submission not valid")
        else:
            # Extract product options from POST
            options = []
            for option in item.options.all():
                if option.code in form.cleaned_data:
                    options.append({'option': option, 'value': form.cleaned_data[option.code]})
            basket.add_product(item, form.cleaned_data['quantity'], options)
            messages.info(self.request, "'%s' (quantity %d) has been added to your basket" %
                          (item.get_title(), form.cleaned_data['quantity']))
 

class LineView(ModelView):
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
    
    def get_model(self):
        basket = basket_factory.get_open_basket(self.request)
        return basket.lines.get(line_reference=self.kwargs['line_reference'])
        
    def handle_POST(self):
        try:
            super(LineView, self).handle_POST()
        except basket_models.Basket.DoesNotExist:
                messages.error(self.request, "You don't have a basket to adjust the lines of")
        except basket_models.Line.DoesNotExist:
            messages.error(self.request, "Unable to find a line with reference %s in your basket" % self.kwargs['line_reference'])
        except basket_models.InvalidBasketLineError, e:
            messages.error(self.request, str(e))
            
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
        
    def do_save_for_later(self, line):
        saved_basket = basket_factory.get_or_create_saved_basket(self.request, self.response)
        saved_basket.merge_line(line)
        msg = "'%s' has been saved for later" % line.product
        messages.info(self.request, msg)
        
       
class SavedLineView(ModelView):
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
    
    def get_model(self):
        basket = basket_factory.get_saved_basket(self.request)
        return basket.lines.get(line_reference=self.kwargs['line_reference'])
        
    def handle_POST(self):
        try:
            super(SavedLineView, self).handle_POST()
        except basket_models.Basket.DoesNotExist:
                messages.error(request, "You don't have a basket to adjust the lines of")
        except basket_models.Line.DoesNotExist:
            messages.error(request, "Unable to find a line with reference %s in your basket" % self.kwargs['line_reference'])
        except basket_models.InvalidBasketLineError, e:
            messages.error(request, str(e))   
            
    def _get_quantity(self):
        if 'quantity' in self.request.POST:
            return int(self.request.POST['quantity'])
        return 0        
            
    def do_move_to_basket(self, line):
        real_basket = basket_factory.get_or_create_open_basket(self.request, self.response)
        real_basket.merge_line(line)
        msg = "'%s' has been moved back to your basket" % line.product
        messages.info(self.request, msg)
        
    def do_delete(self, line):
        line.delete()
        msg = "'%s' has been removed" % line.product
        messages.warn(self.request, msg)
