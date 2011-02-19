Shipping
========

By default, you can configure shipping by using the built-in ShippingMethod models.  These
support shipping charges that are calculated using an order- and item-level charge.

Custom shipping calculators
---------------------------

To use a custom shipping calculator, you need to subclass the core shipping Repository class and
override two methods in provide the calculator of your domain.

First create a ``myshop.shipping`` app and include it in your ``settings.py`` file (removing the ``oscar.shipping``
app in the process.

Next, create ``methods.py`` and create a new ``Repository`` class that subclasses the core ``Repository`` class but
provides the custom behaviour that you need.

Here is an example ``methods.py``::

    from decimal import Decimal

    from oscar.shipping.methods import Repository as CoreRepository
    from oscar.shipping.abstract_models import ShippingMethod
    
    class FixedChargeMethod(ShippingMethod):
        
        name = 'Fixed charge'
        
        def basket_charge_incl_tax(self):
            return Decimal('12.50')
        
        def basket_charge_excl_tax(self):
            return Decimal('12.50')
    
    class Repository(CoreRepository):
        
        def __init__(self):
            self.method = FixedChargeMethod()
        
        def get_shipping_methods(self, user, basket):
            return [self.method] 
    
        def find_by_code(self, code):
            return self.method

Here we are using a plain Python object (not a Django model) as the shipping calculator.