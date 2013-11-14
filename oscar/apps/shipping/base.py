from decimal import Decimal as D
import warnings


class Base(object):
    """
    Shipping method interface class

    This is the superclass to the classes in methods.py, and a de-facto
    superclass to the classes in models.py. This allows using all
    shipping methods interchangeably (aka polymorphism).

    The interface is all properties.
    """

    # CORE INTERFACE
    # --------------

    #: Used to store this method in the session.  Each shipping method should
    #  have a unique code.
    code = '__default__'

    #: The name of the shipping method, shown to the customer during checkout
    name = 'Default shipping'

    #: A more detailed description of the shipping method shown to the customer
    #  during checkout.  Can contain HTML.
    description = ''

    #: Shipping charge including taxes
    charge_excl_tax = D('0.00')

    #: Shipping charge excluding taxes
    charge_incl_tax = None

    #: Whether we now the shipping tax applicable (and hence whether
    #  charge_incl_tax returns a value.
    is_tax_known = False

    # END OF CORE INTERFACE
    # ---------------------

    # These are not intended to be overridden and are used to track shipping
    # discounts.
    is_discounted = False
    discount = D('0.00')

    def _get_tax(self):
        return self.charge_incl_tax - self.charge_excl_tax

    def _set_tax(self, value):
        self.charge_incl_tax = self.charge_excl_tax + value
        self.is_tax_known = True

    tax = property(_get_tax, _set_tax)

    def set_basket(self, basket):
        self.basket = basket

    def basket_charge_excl_tax(self):
        warnings.warn((
            "Use the charge_excl_tax property not basket_charge_excl_tax. "
            "Basket.basket_charge_excl_tax will be removed "
            "in v0.7"),
            DeprecationWarning)
        return self.charge_excl_tax

    def basket_charge_incl_tax(self):
        warnings.warn((
            "Use the charge_incl_tax property not basket_charge_incl_tax. "
            "Basket.basket_charge_incl_tax will be removed "
            "in v0.7"),
            DeprecationWarning)
        return self.charge_incl_tax


# For backwards compatibility, keep an alias called "ShippingMethod"
ShippingMethod = Base
