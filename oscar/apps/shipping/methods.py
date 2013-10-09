from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.base import Base


class Free(Base):
    code = 'free-shipping'
    name = _('Free shipping')
    is_tax_known = True
    charge_incl_tax = charge_excl_tax = D('0.00')


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
        self.charge_excl_tax = charge_excl_tax
        if charge_incl_tax is not None:
            self.charge_incl_tax = charge_incl_tax
            self.is_tax_known = True


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
        return self.get_discount()['discount'] > 0

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
        parent_charge = self.method.charge_incl_tax
        return {
            'offer': self.offer,
            'result': None,
            'name': self.offer.name,
            'description': '',
            'voucher': self.offer.get_voucher(),
            'freq': 1,
            'discount': self.offer.shipping_discount(parent_charge)}

    @property
    def charge_incl_tax_before_discount(self):
        return self.method.charge_incl_tax

    @property
    def charge_excl_tax_before_discount(self):
        return self.method.charge_excl_tax

    @property
    def is_tax_known(self):
        return self.method.is_tax_known

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
        return parent_charge_excl_tax * (charge_incl_tax /
                                         parent_charge_incl_tax)
