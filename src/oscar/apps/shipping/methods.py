from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.core import prices


class Base(object):
    """
    Shipping method interface class

    This is the superclass to the classes in this module. This allows
    using all shipping methods interchangeably (aka polymorphism).

    The interface is all properties.
    """

    #: Used to store this method in the session.  Each shipping method should
    #:  have a unique code.
    code = "__default__"

    #: The name of the shipping method, shown to the customer during checkout
    name = "Default shipping"

    #: A more detailed description of the shipping method shown to the customer
    #:  during checkout.  Can contain HTML.
    description = ""

    #: Whether the charge includes a discount
    is_discounted = False

    def calculate(self, basket):
        """
        Return the shipping charge for the given basket
        """
        raise NotImplementedError

    # pylint: disable=unused-argument
    def discount(self, basket):
        """
        Return the discount on the standard shipping charge
        """
        # The regular shipping methods don't add a default discount.
        # For offers and vouchers, the discount will be provided
        # by a wrapper that Repository.apply_shipping_offer() adds.
        return D("0.00")


class Free(Base):
    """
    This shipping method specifies that shipping is free.
    """

    code = "free-shipping"
    name = _("Free shipping")

    def calculate(self, basket):
        # If the charge is free then tax must be free (musn't it?) and so we
        # immediately set the tax to zero
        return prices.Price(currency=basket.currency, excl_tax=D("0.00"), tax=D("0.00"))


class NoShippingRequired(Free):
    """
    This is a special shipping method that indicates that no shipping is
    actually required (e.g. for digital goods).
    """

    code = "no-shipping-required"
    name = _("No shipping required")


class FixedPrice(Base):
    """
    This shipping method indicates that shipping costs a fixed price and
    requires no special calculation.
    """

    code = "fixed-price-shipping"
    name = _("Fixed price shipping")

    # Charges can be either declared by subclassing and overriding the
    # class attributes or by passing them to the constructor
    charge_excl_tax = None
    charge_incl_tax = None

    def __init__(self, charge_excl_tax=None, charge_incl_tax=None):
        if charge_excl_tax is not None:
            self.charge_excl_tax = charge_excl_tax
        if charge_incl_tax is not None:
            self.charge_incl_tax = charge_incl_tax

    def calculate(self, basket):
        return prices.Price(
            currency=basket.currency,
            excl_tax=self.charge_excl_tax,
            incl_tax=self.charge_incl_tax,
        )


# pylint: disable=abstract-method
class OfferDiscount(Base):
    """
    Wrapper class that applies a discount to an existing shipping
    method's charges.
    """

    is_discounted = True

    def __init__(self, method, offer):
        self.method = method
        self.offer = offer

    # Forwarded properties

    @property
    def code(self):
        """
        Returns the :py:attr:`code <oscar.apps.shipping.methods.Base.code>` of the wrapped shipping method.
        """
        return self.method.code

    @property
    def name(self):
        """
        Returns the :py:attr:`name <oscar.apps.shipping.methods.Base.name>` of the wrapped shipping method.
        """
        return self.method.name

    @property
    def discount_name(self):
        """
        Returns the :py:attr:`name <oscar.apps.offer.abstract_models.BaseOfferMixin.name>` of the applied Offer.
        """
        return self.offer.name

    @property
    def description(self):
        """
        Returns the :py:attr:`description <.Base.description>` of the wrapped shipping method.
        """
        return self.method.description

    def calculate_excl_discount(self, basket):
        """
        Returns the shipping charge for the given basket without
        discount applied.
        """
        return self.method.calculate(basket)


class TaxExclusiveOfferDiscount(OfferDiscount):
    """
    Wrapper class which extends OfferDiscount to be exclusive of tax.
    """

    def calculate(self, basket):
        base_charge = self.method.calculate(basket)
        discount = self.offer.shipping_discount(
            base_charge.excl_tax, base_charge.currency
        )
        excl_tax = base_charge.excl_tax - discount
        return prices.Price(
            currency=base_charge.currency,
            excl_tax=excl_tax,
            tax_code=base_charge.tax_code,
        )

    def discount(self, basket):
        base_charge = self.method.calculate(basket)
        return self.offer.shipping_discount(base_charge.excl_tax, base_charge.currency)


class TaxInclusiveOfferDiscount(OfferDiscount):
    """
    Wrapper class which extends OfferDiscount to be inclusive of tax.
    """

    def calculate(self, basket):
        base_charge = self.method.calculate(basket)
        discount = self.offer.shipping_discount(
            base_charge.incl_tax, base_charge.currency
        )
        incl_tax = base_charge.incl_tax - discount
        excl_tax = self.calculate_excl_tax(base_charge, incl_tax)
        return prices.Price(
            currency=base_charge.currency,
            excl_tax=excl_tax,
            incl_tax=incl_tax,
            tax_code=base_charge.tax_code,
        )

    def calculate_excl_tax(self, base_charge, incl_tax):
        """
        Return the charge excluding tax (but including discount).
        """
        if incl_tax == D("0.00"):
            return D("0.00")
        # We assume we can linearly scale down the excl tax price before
        # discount.
        excl_tax = base_charge.excl_tax * (incl_tax / base_charge.incl_tax)
        return excl_tax.quantize(D("0.01"))

    def discount(self, basket):
        base_charge = self.method.calculate(basket)
        return self.offer.shipping_discount(base_charge.incl_tax, base_charge.currency)
