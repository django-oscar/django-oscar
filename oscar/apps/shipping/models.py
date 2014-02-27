from decimal import Decimal as D

from django.db import models
from django.utils.translation import ugettext_lazy as _

from oscar.apps.shipping import Scales
from oscar.models.fields import AutoSlugField


class ShippingMethod(models.Model):
    # Fields from shipping.base.ShippingMethod must be added here manually.
    code = AutoSlugField(_("Slug"), max_length=128, unique=True,
                         populate_from='name')
    name = models.CharField(_("Name"), max_length=128, unique=True)
    description = models.TextField(_("Description"), blank=True)

    # We allow shipping methods to be linked to a specific set of countries
    countries = models.ManyToManyField('address.Country', null=True,
                                       blank=True, verbose_name=_("Countries"))

    is_discounted = False
    _basket = None

    class Meta:
        abstract = True
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __unicode__(self):
        return self.name

    def set_basket(self, basket):
        self._basket = basket


class OrderAndItemCharges(ShippingMethod):
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

    _basket = None

    class Meta:
        verbose_name = _("Order and Item Charge")
        verbose_name_plural = _("Order and Item Charges")

    @property
    def charge_incl_tax(self):
        """
        Return basket total including tax
        """
        if self.free_shipping_threshold is not None and \
                self._basket.total_incl_tax >= self.free_shipping_threshold:
            return D('0.00')

        charge = self.price_per_order
        for line in self._basket.lines.all():
            if line.product.is_shipping_required:
                charge += line.quantity * self.price_per_item
        return charge

    @property
    def charge_excl_tax(self):
        """
        Return basket total excluding tax.

        Default implementation assumes shipping is tax free.
        """
        return self.charge_incl_tax

    @property
    def is_tax_known(self):
        # We assume tax is known
        return True


class WeightBased(ShippingMethod):
    upper_charge = models.DecimalField(
        _("Upper Charge"), decimal_places=2, max_digits=12, null=True,
        help_text=_("This is the charge when the weight of the basket "
                    "is greater than all the weight bands"""))

    weight_attribute = 'weight'
    default_weight = models.DecimalField(
        _("Default Weight"), decimal_places=2, max_digits=12,
        default=D('0.00'),
        help_text=_("Default product weight in Kg when no weight attribute "
                    "is defined"))

    class Meta:
        verbose_name = _("Weight-based Shipping Method")
        verbose_name_plural = _("Weight-based Shipping Methods")

    @property
    def charge_incl_tax(self):
        # Note, when weighing the basket, we don't check whether the item
        # requires shipping or not.  It is assumed that if something has a
        # weight, then it requires shipping.
        scales = Scales(attribute_code=self.weight_attribute,
                        default_weight=self.default_weight)
        weight = scales.weigh_basket(self._basket)
        band = self.get_band_for_weight(weight)
        if not band:
            if self.bands.all().exists() and self.upper_charge:
                return self.upper_charge
            else:
                return D('0.00')
        return band.charge

    @property
    def charge_excl_tax(self):
        return self.charge_incl_tax

    @property
    def is_tax_known(self):
        # We assume tax is known
        return True

    def get_band_for_weight(self, weight):
        """
        Return the weight band for a given weight
        """
        bands = self.bands.filter(
            upper_limit__gte=weight).order_by('upper_limit')[:1]
        # Query return only one row, so we can evaluate it
        if not bands:
            # No band for this weight
            return None
        return bands[0]


class WeightBand(models.Model):
    """
    Represents a weight band which are used by the WeightBasedShipping method.
    """
    method = models.ForeignKey(WeightBased, related_name='bands',
                               verbose_name=_("Method"))
    upper_limit = models.FloatField(_("Upper Limit"),
                                    help_text=_("""Enter upper limit of this
                                                weight band in Kg, the lower
                                                limit will be determine by the
                                                other weight bands"""))
    charge = models.DecimalField(_("Charge"), decimal_places=2, max_digits=12)

    @property
    def weight_from(self):
        lower_bands = self.method.bands.filter(
            upper_limit__lt=self.upper_limit).order_by('-upper_limit')
        if not lower_bands:
            return D('0.00')
        return lower_bands[0].upper_limit

    @property
    def weight_to(self):
        return self.upper_limit

    class Meta:
        ordering = ['upper_limit']
        verbose_name = _("Weight Band")
        verbose_name_plural = _("Weight Bands")

    def __unicode__(self):
        return _('Charge for weights up to %sKg') % (self.upper_limit,)
