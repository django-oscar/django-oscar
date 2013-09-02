from decimal import Decimal as D
import warnings


class Base(object):
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

    #: Shipping charge including taxes
    charge_excl_tax = D('0.00')

    #: Shipping charge excluding taxes
    charge_incl_tax = None

    def set_basket(self, basket):
        self.basket = basket

    @property
    def basket_charge_excl_tax(self):
        warnings.warn(
            "Use charge_excl_tax not basket_charge_excl_tax",
            DeprecationWarning)
        return self.charge_excl_tax

    @property
    def basket_charge_incl_tax(self):
        warnings.warn(
            "Use charge_incl_tax not basket_charge_incl_tax",
            DeprecationWarning)
        return self.charge_incl_tax


ShippingMethod = Base
