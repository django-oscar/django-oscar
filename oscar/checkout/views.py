from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.core.exceptions import ObjectDoesNotExist

from oscar.services import import_module

basket_factory = import_module('basket.factory', ['get_or_create_open_basket', 'get_open_basket', 
                                                  'get_or_create_saved_basket', 'get_saved_basket'])
checkout_forms = import_module('checkout.forms', ['ShippingAddressForm'])
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker', 'CheckoutSessionData'])
order_models = import_module('order.models', ['ShippingAddress', 'Order', 'Batch', 'BatchLine', 'BatchLinePrice'])
address_models = import_module('address.models', ['UserAddress'])

def prev_steps_must_be_complete(view_fn):
    """
    Decorator fn for checking that previous steps of the checkout
    are complete.
    
    The completed steps (identified by URL-names) are stored in the session.
    If this fails, then we redirect to the next uncompleted step.
    """
    def _view_wrapper(request, *args, **kwargs):
        checker = checkout_utils.ProgressChecker()
        if not checker.are_previous_steps_complete(request):
            messages.error(request, "You must complete this step of the checkout first")
            url_name = checker.get_next_step(request)
            return HttpResponseRedirect(reverse(url_name))
        return view_fn(request, *args, **kwargs)
    return _view_wrapper

def basket_required(view_fn):
    def _view_wrapper(request, *args, **kwargs):
        basket = basket_factory.get_open_basket(request)
        if not basket:
            messages.error(request, "You must add some products to your basket before checking out")
            return HttpResponseRedirect(reverse('oscar-basket'))
        return view_fn(request, *args, **kwargs)
    return _view_wrapper

def mark_step_as_complete(request):
    """ 
    Convenience function for marking a checkout page
    as complete.
    """
    checkout_utils.ProgressChecker().step_complete(request)


class IndexView(object):
    template_file = 'checkout/gateway.html'
    
    def __call__(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('oscar-checkout-shipping-address'))
        return render(request, self.template_file, locals())    

@basket_required
def shipping_address(request):
    """
    Handle the selection of a shipping address.
    """
    co_data = checkout_utils.CheckoutSessionData(request)
    if request.method == 'POST':
        if request.user.is_authenticated and 'address_id' in request.POST:
            address = address_models.UserAddress.objects.get(pk=request.POST['address_id'])
            if 'action' in request.POST and request.POST['action'] == 'ship_to':
                # User has selected a previous address to ship to
                co_data.ship_to_user_address(address)
                mark_step_as_complete(request)
                return HttpResponseRedirect(reverse('oscar-checkout-shipping-method'))
            elif 'action' in request.POST and request.POST['action'] == 'delete':
                address.delete()
                messages.info(request, "Address deleted from your address book")
                return HttpResponseRedirect(reverse('oscar-checkout-shipping-method'))
        else:
            form = checkout_forms.ShippingAddressForm(request.POST)
            if form.is_valid():
                # Address data is valid - store in session and redirect to next step.
                is_default = False
                if 'save_as_default' in request.POST and request.POST['save_as_default'] == 'on':
                    is_default = True
                co_data.ship_to_new_address(form.clean(), is_default)
                mark_step_as_complete(request)
                return HttpResponseRedirect(reverse('oscar-checkout-shipping-method'))
    else:
        addr_fields = co_data.new_address_fields()
        if addr_fields:
            form = checkout_forms.ShippingAddressForm(addr_fields)
        else:
            form = checkout_forms.ShippingAddressForm()
    
    # Add in extra template bindings
    basket = basket_factory.get_open_basket(request)
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    shipping_total_excl_tax = 0
    shipping_total_incl_tax = 0
    
    # Look up address book data
    if request.user.is_authenticated():
        addresses = address_models.UserAddress.objects.filter(user=request.user)
    
    return render(request, 'checkout/shipping_address.html', locals())
    
    
@prev_steps_must_be_complete    
def shipping_method(request):
    """
    Shipping methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    mark_step_as_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-payment'))

@prev_steps_must_be_complete
def payment(request):
    """
    Payment methods are domain-specific and so need implementing in a s
    subclass of this class.
    """
    mark_step_as_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-preview'))

@prev_steps_must_be_complete
def preview(request):
    """
    Show a preview of the order
    """
    co_data = checkout_utils.CheckoutSessionData(request)
    basket = basket_factory.get_open_basket(request)
    
    # Load address data into a blank address model
    addr_data = co_data.new_address_fields()
    if addr_data:
        shipping_addr = order_models.ShippingAddress(**addr_data)
    addr_id = co_data.user_address_id()
    if addr_id:
        shipping_addr = address_models.UserAddress.objects.get(pk=addr_id)
    
    # Calculate order total
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    
    mark_step_as_complete(request)
    return render(request, 'checkout/preview.html', locals())


class SubmitView(object):
    """
    Class for submitting an order.
    
    The class is deliberately split into fine-grained method, responsible for only one
    thing.  This is to make it easier to subclass and override just one component of
    functionality.
    
    Note that the order models support shipping to multiple addresses but the default
    implementation assumes only one.  To change this, override the _get_shipping_address_for_line
    method.
    """
    
    def __call__(self, request):
        
        # Set up the instance variables that are needed to place an order
        self.request = request
        self.co_data = checkout_utils.CheckoutSessionData(request)
        self.basket = basket_factory.get_open_basket(request)
        
        # All the heavy lifting happens here
        order = self._place_order()
        
        # Now, reset the states of the basket and checkout 
        self.basket.set_as_submitted()
        self.co_data.flush()
        checkout_utils.ProgressChecker().all_steps_complete(request)
        
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id
        
        return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))
        
    def _place_order(self):
        """
        Placing an order involves creating all the relevant models based on the
        basket and session data.
        """
        order = self._create_order_model()
        for line in self.basket.lines.all():
            batch = self._get_or_create_batch_for_line(order, line)
            self._create_line_model(order, batch, line)
        return order
        
    def _create_order_model(self):
        """
        Creates an order model.
        """
        calc = checkout_calculators.OrderTotalCalculator(self.request)
        order_data = {'basket': self.basket,
                      'total_incl_tax': calc.order_total_incl_tax(self.basket),
                      'total_excl_tax': calc.order_total_excl_tax(self.basket),
                      'shipping_incl_tax': 0,
                      'shipping_excl_tax': 0,}
        if self.request.user.is_authenticated():
            order_data['user_id'] = self.request.user.id
        order = order_models.Order(**order_data)
        order.save()
        return order
    
    def _create_line_model(self, order, batch, basket_line):
        batch_line = order_models.BatchLine.objects.create(order=order,
                                                           batch=batch, 
                                                           product=basket_line.product, 
                                                           quantity=basket_line.quantity, 
                                                           line_price_excl_tax=basket_line.line_price_excl_tax, 
                                                           line_price_incl_tax=basket_line.line_price_incl_tax)
        self._create_line_price_model(batch_line, basket_line)
        
    def _create_line_price_model(self, batch_line, basket_line):
        order_models.BatchLinePrice.objects.create(line=batch_line, 
                                                   quantity=batch_line.quantity, 
                                                   price_incl_tax=basket_line.unit_price_incl_tax,
                                                   price_excl_tax=basket_line.unit_price_excl_tax)
    
    def _get_or_create_batch_for_line(self, order, line):
         partner = self._get_partner_for_product(line.product)
         shipping_addr = self._get_shipping_address_for_line(line)
         batch,_ = order_models.Batch.objects.get_or_create(order=order, partner=partner, shipping_address=shipping_addr)
         return batch
                
    def _get_partner_for_product(self, product):
        if product.has_stockrecord:
            return product.stockrecord.partner
        raise AttributeError("No partner found for product '%s'" % product)

    def _get_shipping_address_for_line(self, line):
        try:
            addr = self.shipping_addr
        except AttributeError:
            # No cached version - create a shipping address
            addr_data = self.co_data.new_address_fields()
            addr_id = self.co_data.user_address_id()
            if addr_data:
                addr = self._create_shipping_address_from_form_fields(addr_data)
                self._create_user_address(addr_data)
            elif addr_id:
                addr = self._create_shipping_address_from_user_address(addr_id)
            else:
                raise AttributeError("No shipping address data found")
            
            # Cache it as our default behaviour is to have only one
            # shipping address per order.
            self.shipping_addr = addr
        return addr
            
    def _create_shipping_address_from_form_fields(self, addr_data):
        shipping_addr = order_models.ShippingAddress(**addr_data)
        shipping_addr.save() 
        return shipping_addr
    
    def _create_user_address(self, addr_data):
        """
        For signed-in users, we create a user address model which will go 
        into their address book.
        """
        if self.request.user.is_authenticated():
            addr_data['user_id'] = self.request.user.id
            user_addr = address_models.UserAddress(**addr_data)
            # Check that this address isn't already in the db as we don't want
            # to fill up the customer address book with duplicate addresses
            try:
                duplicate_addr = address_models.UserAddress.objects.get(hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                user_addr.save()
    
    def _create_shipping_address_from_user_address(self, addr_id):
        address = address_models.UserAddress.objects.get(pk=addr_id)
        # Increment the number of orders to help determine popularity of orders 
        address.num_orders += 1
        address.save()
        
        shipping_addr = order_models.ShippingAddress()
        address.populate_alternative_model(shipping_addr)
        shipping_addr.save()
        return shipping_addr


def thank_you(request):
    
    try:
        order = order_models.Order.objects.get(pk=request.session['checkout_order_id'])
        del request.session['checkout_order_id']
    except ObjectDoesNotExist:
        return HttpResponseRedirect(reverse('oscar-checkout-index'))
    
    return render(request, 'checkout/thank_you.html', locals())
