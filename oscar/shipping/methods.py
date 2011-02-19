class ShippingMethod(object):
    u"""
    Superclass for all shipping method objects
    """
    code = '__default__'
    name = 'Default shipping'
    description = ''
    
    def set_basket(self, basket):
        self.basket = basket
    
    def basket_charge_incl_tax(self):
        pass
    
    def basket_charge_excl_tax(self):
        pass
    
    
class FreeShipping(ShippingMethod):
    u"""
    Simple method for free shipping
    """
    code = 'free-shipping'
    name = 'Free shipping'
    
    def basket_charge_incl_tax(self):
        return Decimal('0.00')
    
    def basket_charge_excl_tax(self):
        return Decimal('0.00')
       
