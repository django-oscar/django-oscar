from decimal import Decimal as D


class ShippingMethod(object):
    """
    Superclass for all shipping method objects.

    It is an actual superclass to the classes in methods.py, and a de-facto
    superclass to the classes in models.py. This allows using all
    shipping methods interchangeably (aka polymorphism).
    """

    # This is the interface that all shipping methods must implement

    #: Used to store this method in the session.  Each shipping method should
    #  have a unique code.
    code = '__default__'

    #: The name of the shipping method, shown to the customer during checkout
    name = 'Default shipping'

    #: A more detailed description of the shipping method shown to the customer
    # during checkout
    description = ''

    # These are not intended to be overridden
    is_discounted = False
    discount = D('0.00')

    def __init__(self, *args, **kwargs):
        self.exempt_from_tax = False
        super(ShippingMethod, self).__init__(*args, **kwargs)

    def set_basket(self, basket):
        self.basket = basket

    def basket_charge_incl_tax(self):
        """
        Return the shipping charge including any taxes
        """
        raise NotImplemented()

    def basket_charge_excl_tax(self):
        """
        Return the shipping charge excluding taxes
        """
        raise NotImplemented()
