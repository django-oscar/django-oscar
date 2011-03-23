from oscar.shipping.methods import FreeShipping
from oscar.services import import_module

shipping_models = import_module('shipping.models', ['OrderAndItemLevelChargeMethod'])


class Repository(object):
    u"""
    Repository class responsible for returning ShippingMethod
    objects
    """
    
    def get_shipping_methods(self, user, basket, shipping_addr):
        u"""
        Returns all applicable shipping method objects
        for a given basket.
        
        We default to returning the Method models that have been defined but
        this behaviour can easily be overridden by subclassing this class
        and overriding this method.
        """ 
        methods = shipping_models.OrderAndItemLevelChargeMethod.objects.all()
        if not methods.count():
            return [FreeShipping()]
        
        for method in methods:
            method.set_basket(basket)
        return methods

    def find_by_code(self, code):
        u"""
        Returns the appropriate Method object for the given code
        """
        if code == FreeShipping.code:
            return FreeShipping()
        return shipping_models.OrderAndItemLevelChargeMethod.objects.get(code=code)          
