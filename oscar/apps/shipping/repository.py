from oscar.apps.shipping.methods import Free


class Repository(object):
    """
    Repository class responsible for returning ShippingMethod
    objects for a given user, basket etc
    """
    
    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        """
        Return a list of all applicable shipping method objects
        for a given basket.
        
        We default to returning the Method models that have been defined but
        this behaviour can easily be overridden by subclassing this class
        and overriding this method.
        """ 
        methods = [Free()]
        return self.add_basket_to_methods(basket, methods)

    def get_default_shipping_method(self, user, basket, shipping_addr=None, **kwargs):
        return self.get_shipping_methods(user, basket, shipping_addr, **kwargs)[0]

    def add_basket_to_methods(self, basket, methods):
        for method in methods:
            method.set_basket(basket)
        return methods

    def find_by_code(self, code):
        """
        Return the appropriate Method object for the given code
        """
        if code == Free.code:
            return Free()
        return None
