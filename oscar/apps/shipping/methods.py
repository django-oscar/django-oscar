from decimal import Decimal

class ShippingMethod(object):
    u"""
    Superclass for all shipping method objects
    """
    code = '__default__'
    name = 'Default shipping'
    description = ''
    
    def __init__(self):
        self.exempt_from_tax = False
    
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
    

class FixedPriceShipping(ShippingMethod):
    code = 'fixed-price-shipping'
    name = 'Fixed price shipping'
    
    def __init__(self, charge_incl_tax, charge_excl_tax=None):
        self.charge_incl_tax = charge_incl_tax
        if not charge_excl_tax:
            charge_excl_tax = charge_incl_tax
        self.charge_excl_tax = charge_excl_tax
    
    def basket_charge_incl_tax(self):
        return self.charge_incl_tax
    
    def basket_charge_excl_tax(self):
        return self.charge_excl_tax
