from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, render
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from oscar.views import ModelView
from oscar.services import import_module

basket_models = import_module('basket.models', ['Basket', 'Line', 'InvalidBasketLineError'])
basket_forms = import_module('basket.forms', ['FormFactory'])
basket_factory = import_module('basket.factory', ['BasketFactory'])
basket_signals = import_module('basket.signals', ['basket_addition'])
product_models = import_module('product.models', ['Item'])
offer_models = import_module('offer.models', ['Voucher'])
    
        
class BasketView(ModelView):
    u"""Class-based view for the basket model."""
    template_file = 'basket/summary.html'
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
        self.factory = basket_factory.BasketFactory()
    
    def get_model(self):
        u"""Return a basket model"""
        return self.factory.get_or_create_open_basket(self.request, self.response)
    
    def handle_GET(self, basket):
        u"""Handle GET requests against the basket"""
        saved_basket = self.factory.get_saved_basket(self.request)
        self.response = render(self.request, self.template_file, locals())
        
    def handle_POST(self, basket):
        u"""Handle POST requests against the basket"""
        try:
            super(BasketView, self).handle_POST(basket)
        except basket_models.InvalidBasketLineError, e:
            # We handle InvalidBasketLineError gracefully as it will be domain logic
            # which causes this to be thrown (eg. a product out of stock)
            messages.error(self.request, str(e))
            
    def do_flush(self, basket):
        u"""Flush basket content"""
        basket.flush()
        messages.info(self.request, "Your basket has been emptied")
        
    def do_add(self, basket):
        u"""Add an item to the basket"""
        item = get_object_or_404(product_models.Item.objects, pk=self.request.POST['product_id'])
        
        # Send signal so analytics can track this event.  Note that be emitting
        # the signal here, we do not track quantity changes to a product - only
        # the initial "add".
        basket_signals.basket_addition.send(sender=self, product=item, user=self.request.user)
        
        factory = basket_forms.FormFactory()
        form = factory.create(item, self.request.POST)
        if not form.is_valid():
            self.response = HttpResponseRedirect(item.get_absolute_url())
            messages.error(self.request, "Unable to add your item to the basket - submission not valid")
        else:
            # Extract product options from POST
            options = []
            for option in item.options:
                if option.code in form.cleaned_data:
                    options.append({'option': option, 'value': form.cleaned_data[option.code]})
            basket.add_product(item, form.cleaned_data['quantity'], options)
            messages.info(self.request, "'%s' (quantity %d) has been added to your basket" %
                          (item.get_title(), form.cleaned_data['quantity']))
    
    def do_add_voucher(self, basket):
        code = self.request.POST['voucher_code']
        try:
            voucher = offer_models.Voucher._default_manager.get(code=code)
            basket.vouchers.add(voucher)
            basket.save()
            messages.info(self.request, "Voucher '%s' added to basket" % voucher.code)
        except ObjectDoesNotExist:
            messages.error(self.request, "No voucher found with code '%s'" % code)
            
    def do_remove_voucher(self, basket):
        code = self.request.POST['voucher_code']
        try:
            voucher = basket.vouchers.get(code=code)
            basket.vouchers.remove(voucher)
            basket.save()
            messages.info(self.request, "Voucher '%s' removed from basket" % voucher.code)
        except ObjectDoesNotExist:
            messages.error(self.request, "No voucher found with code '%s'" % code)
 

class LineView(ModelView):
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
        self.factory = basket_factory.BasketFactory()
    
    def get_model(self):
        u"""Get basket lines"""
        basket = self.factory.get_open_basket(self.request)
        return basket.lines.get(line_reference=self.kwargs['line_reference'])
        
    def handle_POST(self, line):
        u"""Handle POST requests against the basket line"""
        try:
            super(LineView, self).handle_POST(line)
        except basket_models.Basket.DoesNotExist:
                messages.error(self.request, "You don't have a basket to adjust the lines of")
        except basket_models.Line.DoesNotExist:
            messages.error(self.request, "Unable to find a line with reference %s in your basket" % self.kwargs['line_reference'])
        except basket_models.InvalidBasketLineError, e:
            messages.error(self.request, str(e))
            
    def _get_quantity(self):
        u"""Get item quantity"""
        if 'quantity' in self.request.POST:
            return int(self.request.POST['quantity'])
        return 0        
            
    def do_increment_quantity(self, line):
        u"""Increment item quantity"""
        q = self._get_quantity()
        line.quantity += q
        line.save()    
        msg = "The quantity of '%s' has been increased by %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_decrement_quantity(self, line):
        u"""Decrement item quantity"""
        q = self._get_quantity()
        line.quantity -= q
        line.save()    
        msg = "The quantity of '%s' has been decreased by %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_set_quantity(self, line):
        u"""Set an item quantity"""
        q = self._get_quantity()
        line.quantity = q
        line.save()    
        msg = "The quantity of '%s' has been set to %d" % (line.product, q)
        messages.info(self.request, msg)
        
    def do_delete(self, line):
        u"""Delete a basket item"""
        line.delete()
        msg = "'%s' has been removed from your basket" % line.product
        messages.info(self.request, msg)
        
    def do_save_for_later(self, line):
        u"""Save basket for later use"""
        saved_basket = self.factory.get_or_create_saved_basket(self.request, self.response)
        saved_basket.merge_line(line)
        msg = "'%s' has been saved for later" % line.product
        messages.info(self.request, msg)
        
       
class SavedLineView(ModelView):
    
    def __init__(self):
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
        self.factory = basket_factory.BasketFactory()
    
    def get_model(self):
        basket = self.factory.get_saved_basket(self.request)
        return basket.lines.get(line_reference=self.kwargs['line_reference'])
        
    def handle_POST(self, line):
        u"""Handle POST requests against a saved line"""
        try:
            super(SavedLineView, self).handle_POST(line)
        except basket_models.InvalidBasketLineError, e:
            messages.error(request, str(e))   
            
    def do_move_to_basket(self, line):
        u"""Merge line items in to current basket"""
        real_basket = self.factory.get_or_create_open_basket(self.request, self.response)
        real_basket.merge_line(line)
        msg = "'%s' has been moved back to your basket" % line.product
        messages.info(self.request, msg)
        
    def do_delete(self, line):
        u"""Delete line item"""
        line.delete()
        msg = "'%s' has been removed" % line.product
        messages.warn(self.request, msg)
        
    def _get_quantity(self):
        u"""Get line item quantity"""
        if 'quantity' in self.request.POST:
            return int(self.request.POST['quantity'])
        return 0
