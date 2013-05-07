from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping.base import ShippingMethod


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


class OfferDiscount(ShippingMethod):
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
        parent_charge = self.method.basket_charge_incl_tax()
        return {
            'offer': self.offer,
            'result': None,
            'name': self.offer.name,
            'description': '',
            'voucher': self.offer.get_voucher(),
            'freq': 1,
            'discount': self.offer.shipping_discount(parent_charge)}

    def basket_charge_incl_tax_before_discount(self):
        return self.method.basket_charge_incl_tax()

    def basket_charge_excl_tax_before_discount(self):
        return self.method.basket_charge_excl_tax()

    def basket_charge_incl_tax(self):
        parent_charge = self.method.basket_charge_incl_tax()
        discount = self.offer.shipping_discount(parent_charge)
        return parent_charge - discount

    def basket_charge_excl_tax(self):
        # Adjust tax exclusive rate using the ratio of the two tax inclusive
        # charges.
        parent_charge_excl_tax = self.method.basket_charge_excl_tax()
        parent_charge_incl_tax = self.method.basket_charge_incl_tax()
        charge_incl_tax = self.basket_charge_incl_tax()
        if parent_charge_incl_tax == 0:
            return D('0.00')
        return parent_charge_excl_tax * (charge_incl_tax /
                                         parent_charge_incl_tax)
