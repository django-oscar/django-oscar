from decimal import Decimal as D


class ShippingMethod(object):
    """
    Superclass for all shipping method objects.

    It is an actual superclass to the classes in methods.py, and a de-facto
    superclass to the classes in models.py. This allows using all
    shipping methods interchangeably (aka polymorphism).
    """

    # This is the interface that all shipping methods must implement

    code = '__default__'
    name = 'Default shipping'
    description = ''
    is_discounted = False
    discount = D('0.00')

    def __init__(self, *args, **kwargs):
        self.exempt_from_tax = False
        super(ShippingMethod, self).__init__(*args, **kwargs)

    def set_basket(self, basket):
        self.basket = basket

    def basket_charge_incl_tax(self):
        pass

    def basket_charge_excl_tax(self):
        pass
