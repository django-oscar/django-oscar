from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _

from oscar.core import prices


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

    # END OF CORE INTERFACE
    # ---------------------

    # These are not intended to be overridden and are used to track shipping
    # discounts.
    #is_discounted = False
    #discount = D('0.00')

    def calculate(self, basket):
        """
        Return the shipping charge for the given basket
        """
        raise NotImplemented()

    # Tax - we use a property with a getter and a setter. When tax is only
    # known later on, it can be assigned directly to the tax attribute.

    #def _get_tax(self):
    #    return self.charge_incl_tax - self.charge_excl_tax

    #def _set_tax(self, value):
    #    # Tax can be set later on in territories where it is now known up
    #    # front.
    #    self.charge_incl_tax = self.charge_excl_tax + value
    #    self.is_tax_known = True

    #tax = property(_get_tax, _set_tax)

    #def set_basket(self, basket):
    #    self.basket = basket


class Free(Base):
    code = 'free-shipping'
    name = _('Free shipping')

    def calculate(self, basket):
        # If the charge is free then tax must be free (musn't it?) and so we
        # immediately set the tax to zero
        return prices.Price(
            currency=basket.currency,
            excl_tax=D('0.00'), tax=D('0.00'))


class NoShippingRequired(Free):
    """
    This is a special shipping method that indicates that no shipping is
    actually required (eg for digital goods).
    """
    code = 'no-shipping-required'
    name = _('No shipping required')


class FixedPrice(Base):
    code = 'fixed-price-shipping'
    name = _('Fixed price shipping')

    def __init__(self, charge_excl_tax, charge_incl_tax=None):
        self._excl_tax = charge_excl_tax
        self._incl_tax = charge_incl_tax

    def calculate(self, basket):
        return prices.Price(
            currency=basket.currency,
            excl_tax=self._excl_tax,
            incl_tax=self._incl_tax)


class OfferDiscount(Base):
    """
    Wrapper class that applies a discount to an existing shipping method's
    charges
    """

    def __init__(self, method, offer):
        self.method = method
        self.offer = offer

    @property
    def is_discounted(self):
        # We check to see if the discount is non-zero.  It is possible to have
        # zero shipping already in which case this the offer does not lead to
        # any further discount.
        return self.discount > 0

    @property
    def discount(self):
        return self.get_discount()['discount']

    @property
    def code(self):
        return self.method.code

    @property
    def name(self):
        return self.method.name

    @property
    def description(self):
        return self.method.description

    def get_discount(self):
        # Return a 'discount' dictionary in the same form as that used by the
        # OfferApplications class
        return {
            'offer': self.offer,
            'result': None,
            'name': self.offer.name,
            'description': '',
            'voucher': self.offer.get_voucher(),
            'freq': 1,
            'discount': self.effective_discount}

    @property
    def charge_incl_tax_before_discount(self):
        return self.method.charge_incl_tax

    @property
    def charge_excl_tax_before_discount(self):
        return self.method.charge_excl_tax

    # Property for is_tax_known

    def _get_is_tax_known(self):
        return self.method.is_tax_known

    def _set_is_tax_known(self, value):
        self.method.is_tax_known = value

    is_tax_known = property(_get_is_tax_known, _set_is_tax_known)

    @property
    def effective_discount(self):
        """
        The discount value.
        """
        raise NotImplemented()

    @property
    def charge_excl_tax(self):
        raise NotImplemented()


class TaxExclusiveOfferDiscount(OfferDiscount):

    @property
    def effective_discount(self):
        parent_charge = self.method.charge_excl_tax
        return self.offer.shipping_discount(parent_charge)

    @property
    def charge_excl_tax(self):
        parent_charge = self.method.charge_excl_tax
        discount = self.offer.shipping_discount(parent_charge)
        return parent_charge - discount


class TaxInclusiveOfferDiscount(OfferDiscount):

    @property
    def effective_discount(self):
        parent_charge = self.method.charge_incl_tax
        return self.offer.shipping_discount(parent_charge)

    @property
    def charge_incl_tax(self):
        parent_charge = self.method.charge_incl_tax
        discount = self.offer.shipping_discount(parent_charge)
        return parent_charge - discount

    @property
    def charge_excl_tax(self):
        # Adjust tax exclusive rate using the ratio of the two tax inclusive
        # charges.
        parent_charge_excl_tax = self.method.charge_excl_tax
        parent_charge_incl_tax = self.method.charge_incl_tax
        charge_incl_tax = self.charge_incl_tax
        if parent_charge_incl_tax == 0:
            return D('0.00')
        charge = parent_charge_excl_tax * (charge_incl_tax /
                                           parent_charge_incl_tax)
        return charge.quantize(D('0.01'))
