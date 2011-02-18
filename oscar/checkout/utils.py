from django.core.urlresolvers import resolve

from oscar.services import import_module

shipping_models = import_module('shipping.models', ['Method'])


class ProgressChecker(object):
    u"""
    Class for testing whether the appropriate steps of the checkout
    have been completed.
    """
    
    # List of URL names that have to be completed (in this order)
    urls_for_steps = ['oscar-checkout-shipping-address',
                      'oscar-checkout-shipping-method',
                      'oscar-checkout-payment-method',
                      'oscar-checkout-preview',
                      'oscar-checkout-payment-details',
                      'oscar-checkout-submit',]
    
    def are_previous_steps_complete(self, request):
        u"""
        Checks whether the previous checkout steps have been completed.
        
        This uses the URL-name and the class-level list of required
        steps.
        """
        # Extract the URL name from the path
        complete_steps = self._get_completed_steps(request)
        try:
            url_name = self._get_url_name(request)
            current_step_index = self.urls_for_steps.index(url_name)
            last_completed_step_index = len(complete_steps) - 1
            return current_step_index <= last_completed_step_index + 1 
        except ValueError:
            # Can't find current step index - must be manipulation
            return False
        except IndexError:
            # No complete steps - only allowed to be on first page
            return current_step_index == 0
            
    def step_complete(self, request):
        u"""Record a checkout step as complete."""
        url_name = self._get_url_name(request)
        complete_steps = self._get_completed_steps(request)
        if not url_name in complete_steps:
            # Only add name if this is the first time the step 
            # has been completed. 
            complete_steps.append(url_name)
            request.session['checkout_complete_steps'] = complete_steps 
            
    def get_next_step(self, request):
        u"""Returns the next incomplete step of the checkout."""
        completed_steps = self._get_completed_steps(request)
        if len(completed_steps):
            return self.urls_for_steps[len(completed_steps)]  
        else: 
            return self.urls_for_steps[0]
            
    def all_steps_complete(self, request):
        u"""
        Order has been submitted - clear the completed steps from 
        the session.
        """
        request.session['checkout_complete_steps'] = []
        
    def _get_url_name(self, request):    
        return resolve(request.path).url_name
        
    def _get_completed_steps(self, request):
        return request.session.get('checkout_complete_steps', [])
    

class CheckoutSessionData(object):
    u"""Class responsible for marshalling all the checkout session data."""
    SESSION_KEY = 'checkout_data'
    FREE_SHIPPING = '__free__'
    
    def __init__(self, request):
        self.request = request
        if self.SESSION_KEY not in self.request.session:
            self.request.session[self.SESSION_KEY] = {}
    
    def _check_namespace(self, namespace):
        if namespace not in self.request.session[self.SESSION_KEY]:
            self.request.session[self.SESSION_KEY][namespace] = {}
          
    def _get(self, namespace, key):
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            return self.request.session[self.SESSION_KEY][namespace][key]
        return None
            
    def _set(self, namespace, key, value):
        self._check_namespace(namespace)
        self.request.session[self.SESSION_KEY][namespace][key] = value
        self.request.session.modified = True
        
    def _unset(self, namespace, key):
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            del self.request.session[self.SESSION_KEY][namespace][key]
            self.request.session.modified = True
            
    def flush(self):
        self.request.session[self.SESSION_KEY] = {}
        
    # Shipping methods    
        
    def ship_to_user_address(self, address):
        self._set('shipping', 'user_address_id', address.id)
        self._unset('shipping', 'new_address_fields')
        
    def ship_to_new_address(self, address_fields):
        self._set('shipping', 'new_address_fields', address_fields)
        self._unset('shipping', 'user_address_id')
        
    def new_address_fields(self):
        return self._get('shipping', 'new_address_fields')
        
    def user_address_id(self):
        return self._get('shipping', 'user_address_id')
    
    def use_free_shipping(self):
        self._set('shipping', 'method_code', '__free__')
    
    def use_shipping_method(self, code):
        self._set('shipping', 'method_code', code)
        
    def shipping_method(self):
        u"""
        Returns the shipping method model based on the 
        data stored in the session.
        """
        code = self._get('shipping', 'method_code')
        if code == self.FREE_SHIPPING:
            method = shipping_models.Method(name="Standard shipping (Free)", code=self.FREE_SHIPPING)
        else:
            method = shipping_models.Method.objects.get(code=code)
        return method