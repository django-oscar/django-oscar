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

    #: Used to store this method in the session.  Each shipping method should
    #  have a unique code.
    code = '__default__'

    #: The name of the shipping method, shown to the customer during checkout
    name = 'Default shipping'

    #: A more detailed description of the shipping method shown to the customer
    #  during checkout.  Can contain HTML.
    description = ''

    def calculate(self, basket):
        """
        Return the shipping charge for the given basket
        """
        raise NotImplemented()


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

    # Forwarded properties

    @property
    def code(self):
        return self.method.code

    @property
    def name(self):
        return self.method.name

    @property
    def description(self):
        return self.method.description

    #@property
    #def is_discounted(self):
    #    # We check to see if the discount is non-zero.  It is possible to have
    #    # zero shipping already in which case this the offer does not lead to
    #    # any further discount.
    #    return self.discount > 0

    #@property
    #def discount(self):
    #    return self.get_discount()['discount']

    #def get_discount(self):
    #    # Return a 'discount' dictionary in the same form as that used by the
    #    # OfferApplications class
    #    return {
    #        'offer': self.offer,
    #        'result': None,
    #        'name': self.offer.name,
    #        'description': '',
    #        'voucher': self.offer.get_voucher(),
    #        'freq': 1,
    #        'discount': self.effective_discount}

    @property
    def effective_discount(self):
        """
        The discount value.
        """
        raise NotImplemented()


class TaxExclusiveOfferDiscount(OfferDiscount):

    def calculate(self, basket):
        base_charge = self.method.calculate(basket)
        discount = self.offer.shipping_discount(base_charge.excl_tax)
        excl_tax = base_charge.excl_tax - discount
        return prices.Price(
            currency=base_charge.currency,
            excl_tax=excl_tax)

    @property
    def effective_discount(self):
        parent_charge = self.method.charge_excl_tax
        return self.offer.shipping_discount(parent_charge)


class TaxInclusiveOfferDiscount(OfferDiscount):

    def calculate(self, basket):
        base_charge = self.method.calculate(basket)
        discount = self.offer.shipping_discount(base_charge.incl_tax)
        incl_tax = base_charge.incl_tax - discount
        excl_tax = self.calculate_excl_tax(base_charge, incl_tax)
        return prices.Price(
            currency=base_charge.currency,
            excl_tax=excl_tax, incl_tax=incl_tax)

    def calculate_excl_tax(self, base_charge, incl_tax):
        """
        Return the charge excluding tax (but including discount).
        """
        if incl_tax == D('0.00'):
            return D('0.00')
        # We assume we can linearly scale down the excl tax price before
        # discount.
        excl_tax = base_charge.excl_tax * (incl_tax /
                                           base_charge.incl_tax)
        return excl_tax.quantize(D('0.01'))

    #@property
    #def effective_discount(self):
    #    parent_charge = self.method.charge_incl_tax
    #    return self.offer.shipping_discount(parent_charge)
