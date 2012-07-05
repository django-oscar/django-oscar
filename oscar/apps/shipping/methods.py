from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.base import ShippingMethod
from oscar.apps.shipping.models import OrderAndItemCharges, WeightBand, WeightBased
from oscar.apps.shipping import Scales


class Free(ShippingMethod):
    """
    Simple method for free shipping
    """
    code = 'free-shipping'
    name = _('Free shipping')
    
    def basket_charge_incl_tax(self):
        return D('0.00')
    
    def basket_charge_excl_tax(self):
        return D('0.00')


class NoShippingRequired(Free):
    code = 'no-shipping-required'
    name = _('No shipping required')
    

class FixedPrice(ShippingMethod):
    code = 'fixed-price-shipping'
    name = _('Fixed price shipping')
    
    def __init__(self, charge_incl_tax, charge_excl_tax=None):
        self.charge_incl_tax = charge_incl_tax
        if not charge_excl_tax:
            charge_excl_tax = charge_incl_tax
        self.charge_excl_tax = charge_excl_tax
    
    def basket_charge_incl_tax(self):
        return self.charge_incl_tax
    
    def basket_charge_excl_tax(self):
        return self.charge_excl_tax

