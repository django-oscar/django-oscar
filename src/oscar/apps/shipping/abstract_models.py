# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from oscar.core import prices
from oscar.models.fields import AutoSlugField


@python_2_unicode_compatible
class AbstractBase(models.Model):
    """
    Implements the interface declared by shipping.base.Base
    """
    code = AutoSlugField(_("Slug"), max_length=128, unique=True,
                         populate_from='name')
    name = models.CharField(_("Name"), max_length=128, unique=True)
    description = models.TextField(_("Description"), blank=True)

    # We allow shipping methods to be linked to a specific set of countries
    countries = models.ManyToManyField('address.Country',
                                       blank=True, verbose_name=_("Countries"))

    # We need this to mimic the interface of the Base shipping method
    is_discounted = False

    class Meta:
        abstract = True
        app_label = 'shipping'
        ordering = ['name']
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __str__(self):
        return self.name


class AbstractOrderAndItemCharges(AbstractBase):
    """
    Standard shipping method

    This method has two components:
    * a charge per order
    * a charge per item

    Many sites use shipping logic which fits into this system.  However, for
    more complex shipping logic, a custom shipping method object will need to
    be provided that subclasses ShippingMethod.
    """
    price_per_order = models.DecimalField(
        _("Price per order"), decimal_places=2, max_digits=12,
        default=D('0.00'))
    price_per_item = models.DecimalField(
        _("Price per item"), decimal_places=2, max_digits=12,
        default=D('0.00'))

    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(
        _("Free Shipping"), decimal_places=2, max_digits=12, blank=True,
        null=True)

    class Meta(AbstractBase.Meta):
        abstract = True
        app_label = 'shipping'
        verbose_name = _("Order and Item Charge")
        verbose_name_plural = _("Order and Item Charges")

    def calculate(self, basket):
        if (self.free_shipping_threshold is not None and
                basket.total_incl_tax >= self.free_shipping_threshold):
            return prices.Price(
                currency=basket.currency, excl_tax=D('0.00'),
                incl_tax=D('0.00'))

        charge = self.price_per_order
        for line in basket.lines.all():
            if line.product.is_shipping_required:
                charge += line.quantity * self.price_per_item

        # Zero tax is assumed...
        return prices.Price(
            currency=basket.currency,
            excl_tax=charge,
            incl_tax=charge)
