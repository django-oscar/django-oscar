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
checkout_forms = import_module('checkout.forms', ['DeliveryAddressForm'])
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker'])
order_models = import_module('order.models', ['DeliveryAddress', 'Order'])
address_models = import_module('address.models', ['UserAddress'])

class CheckoutSessionData(object):
    """
    Class responsible for marshalling all the checkout session data.
    """
    session_key = 'checkout_data'
    
    def __init__(self, request):
        self.request = request
        if self.session_key not in self.request.session:
            self.request.session[self.session_key] = {}
    
    def _check_namespace(self, namespace):
        if namespace not in self.request.session[self.session_key]:
            self.request.session[self.session_key][namespace] = {}
          
    def _get(self, namespace, key):
        self._check_namespace(namespace)
        if key in self.request.session[self.session_key][namespace]:
            return self.request.session[self.session_key][namespace][key]
        return None
            
    def _set(self, namespace, key, value):
        self._check_namespace(namespace)
        self.request.session[self.session_key][namespace][key] = value
        self.request.session.modified = True
        
    def _unset(self, namespace, key):
        self._check_namespace(namespace)
        if key in self.request.session[self.session_key][namespace]:
            del self.request.session[self.session_key][namespace][key]
            self.request.session.modified = True
            
    def flush(self):
        self.request.session[self.session_key] = {}
        
    # Delivery methods    
        
    def deliver_to_user_address(self, address):
        self._set('delivery', 'user_address_id', address.id)
        self._unset('delivery', 'new_address_fields')
        self._unset('delivery', 'is_default')
        
    def deliver_to_new_address(self, address_fields, is_default=False):
        self._set('delivery', 'new_address_fields', address_fields)
        self._set('delivery', 'is_default', is_default)
        self._unset('delivery', 'user_address_id')
        
    def new_address_fields(self):
        return self._get('delivery', 'new_address_fields')
        
    def user_address_id(self):
        return self._get('delivery', 'user_address_id')
    
    def should_new_address_be_default(self):
        return self._get('delivery', 'is_default') == True
        

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


def mark_step_as_complete(request):
    """ 
    Convenience function for marking a checkout page
    as complete.
    """
    checkout_utils.ProgressChecker().step_complete(request)

def basket_required(view_fn):
    def _view_wrapper(request, *args, **kwargs):
        basket = basket_factory.get_open_basket(request)
        if not basket:
            messages.error(request, "You must add some products to your basket before checking out")
            return HttpResponseRedirect(reverse('oscar-basket'))
        return view_fn(request, *args, **kwargs)
    return _view_wrapper




def index(request):
    """
    Need to check here if the user is ready to start the checkout
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('oscar-checkout-delivery-address'))
    return render(request, 'checkout/gateway.html', locals())

@basket_required
def delivery_address(request):
    """
    Handle the selection of a delivery address.
    """
    co_data = CheckoutSessionData(request)
    if request.method == 'POST':
        if request.user.is_authenticated and 'address_id' in request.POST:
            address = address_models.UserAddress.objects.get(pk=request.POST['address_id'])
            if 'action' in request.POST and request.POST['action'] == 'deliver_to':
                # User has selected a previous address to deliver to
                co_data.deliver_to_user_address(address)
                mark_step_as_complete(request)
                return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
            elif 'action' in request.POST and request.POST['action'] == 'delete':
                address.delete()
                messages.info(request, "Address deleted from your address book")
                return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
        else:
            form = checkout_forms.DeliveryAddressForm(request.POST)
            if form.is_valid():
                # Address data is valid - store in session and redirect to next step.
                is_default = False
                if 'save_as_default' in request.POST and request.POST['save_as_default'] == 'on':
                    is_default = True
                co_data.deliver_to_new_address(form.clean(), is_default)
                mark_step_as_complete(request)
                return HttpResponseRedirect(reverse('oscar-checkout-delivery-method'))
    else:
        addr_fields = co_data.new_address_fields()
        if addr_fields:
            form = checkout_forms.DeliveryAddressForm(addr_fields)
        else:
            form = checkout_forms.DeliveryAddressForm()
    
    # Add in extra template bindings
    basket = basket_factory.get_open_basket(request)
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    delivery_total_excl_tax = 0
    delivery_total_incl_tax = 0
    
    # Look up address book data
    if request.user.is_authenticated():
        addresses = address_models.UserAddress.objects.filter(user=request.user)
    
    return render(request, 'checkout/delivery_address.html', locals())
    
    
@prev_steps_must_be_complete    
def delivery_method(request):
    """
    Delivery methods are domain-specific and so need implementing in a 
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
    co_data = CheckoutSessionData(request)
    basket = basket_factory.get_open_basket(request)
    
    # Load address data into a blank address model
    addr_data = co_data.new_address_fields()
    if addr_data:
        delivery_addr = order_models.DeliveryAddress(**addr_data)
    addr_id = co_data.user_address_id()
    if addr_id:
        delivery_addr = address_models.UserAddress.objects.get(pk=addr_id)
    
    # Calculate order total
    calc = checkout_calculators.OrderTotalCalculator(request)
    order_total = calc.order_total_incl_tax(basket)
    
    mark_step_as_complete(request)
    return render(request, 'checkout/preview.html', locals())

@prev_steps_must_be_complete
def submit(request):
    """
    Do several things then redirect to the thank-you page
    """
    co_data = CheckoutSessionData(request)
    
    # Save the address data
    addr_data = co_data.new_address_fields()
    if addr_data:
        # A new delivery address has been entered
        delivery_addr = order_models.DeliveryAddress(**addr_data)
        delivery_addr.save()
        
        # Save a new user address
        if request.user.is_authenticated():
            addr_data['user_id'] = request.user.id
            user_addr = address_models.UserAddress(**addr_data)
            # Check that this address isn't already in the db
            try:
                duplicate_addr = address_models.UserAddress.objects.get(hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                if co_data.should_new_address_be_default():
                    user_addr.is_primary = True 
                user_addr.save()
            
    addr_id = co_data.user_address_id()
    if addr_id:
        # A previously used address has been selected.  We need to convert it
        # to a delivery address and save it
        address = address_models.UserAddress.objects.get(pk=addr_id)
        delivery_addr = order_models.DeliveryAddress()
        address.populate_alternative_model(delivery_addr)
        delivery_addr.save()
    
    # Save the order model
    calc = checkout_calculators.OrderTotalCalculator(request)
    basket = basket_factory.get_open_basket(request)
    order_data = {'basket': basket,
                  'total_incl_tax': calc.order_total_incl_tax(basket),
                  'total_excl_tax': calc.order_total_excl_tax(basket),
                  'shipping_incl_tax': 0,
                  'shipping_excl_tax': 0,}
    if request.user.is_authenticated():
        order_data['user_id'] = request.user.id
    order = order_models.Order(**order_data).save()
    
    # @todo set basket as submitted
    basket.set_as_submitted()
    
    # @todo unset all session data
    co_data.flush()
    
    # @todo Save order id in session so thank-you page can load it
    checkout_utils.ProgressChecker().all_steps_complete(request)
    return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))


def thank_you(request):
    return render(request, 'checkout/thank_you.html', locals())