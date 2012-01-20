class ShippingMethod(object):
    """
    Superclass for all shipping method objects
    """
    code = '__default__'
    name = 'Default shipping'
    description = ''
    
    def __init__(self, *args, **kwargs):
        self.exempt_from_tax = False
        super(ShippingMethod, self).__init__(*args, **kwargs)
    
    def set_basket(self, basket):
        self.basket = basket
    
    def basket_charge_incl_tax(self):
        pass
    
    def basket_charge_excl_tax(self):
        pass
