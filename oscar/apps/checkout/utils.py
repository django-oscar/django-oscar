from django.core.urlresolvers import resolve

from oscar.core.loading import import_module

import_module('shipping.repository', ['Repository'], locals())


class CheckoutSessionData(object):
    u"""Class responsible for marshalling all the checkout session data."""
    SESSION_KEY = 'checkout_data'
    
    def __init__(self, request):
        self.request = request
        if self.SESSION_KEY not in self.request.session:
            self.request.session[self.SESSION_KEY] = {}
    
    def _check_namespace(self, namespace):
        if namespace not in self.request.session[self.SESSION_KEY]:
            self.request.session[self.SESSION_KEY][namespace] = {}
          
    def _get(self, namespace, key):
        u"""Return session value or None"""
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            return self.request.session[self.SESSION_KEY][namespace][key]
        return None
            
    def _set(self, namespace, key, value):
        u"""Set session value"""
        self._check_namespace(namespace)
        self.request.session[self.SESSION_KEY][namespace][key] = value
        self.request.session.modified = True
        
    def _unset(self, namespace, key):
        u"""Unset session value"""
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            del self.request.session[self.SESSION_KEY][namespace][key]
            self.request.session.modified = True
            
    def flush(self):
        u"""Delete session key"""
        self.request.session[self.SESSION_KEY] = {}
        
    # Shipping methods    
        
    def ship_to_user_address(self, address):
        u"""Set existing shipping address id to session and unset address fields from session"""
        self._set('shipping', 'user_address_id', address.id)
        self._unset('shipping', 'new_address_fields')
        
    def ship_to_new_address(self, address_fields):
        u"""Set new shipping address details to session and unset shipping address id"""
        self._set('shipping', 'new_address_fields', address_fields)
        self._unset('shipping', 'user_address_id')
        
    def new_address_fields(self):
        u"""Get shipping address fields from session"""
        return self._get('shipping', 'new_address_fields')
        
    def user_address_id(self):
        u"""Get user address id from session"""
        return self._get('shipping', 'user_address_id')
    
    def use_free_shipping(self):
        u"""Set "free shipping" code to session"""
        self._set('shipping', 'method_code', '__free__')
    
    def use_shipping_method(self, code):
        u"""Set shipping method code to session"""
        self._set('shipping', 'method_code', code)
        
    def shipping_method(self):
        u"""
        Returns the shipping method model based on the 
        data stored in the session.
        """
        code = self._get('shipping', 'method_code')
        if not code:
            return None
        return Repository().find_by_code(code)
    
    # Payment methods
    
    def pay_by(self, method):
        self._set('payment', 'method', method)
        
    def payment_method(self):
        return self._get('payment', 'method')
        
