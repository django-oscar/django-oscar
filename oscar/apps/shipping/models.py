from decimal import Decimal as D

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.conf import settings


class ShippingMethod(models.Model):
    code = models.SlugField(max_length=128, unique=True)
    name = models.CharField(_("Name"), max_length=128, unique=True)
    description = models.TextField(_("Description"), blank=True)

    _basket = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(ShippingMethod, self).save(*args, **kwargs)

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
    
    Many sites use shipping logic which fits into this system.  However, for more
    complex shipping logic, a custom shipping method object will need to be provided
    that subclasses ShippingMethod.
    """
    price_per_order = models.DecimalField(decimal_places=2, max_digits=12, default=D('0.00'))
    price_per_item = models.DecimalField(decimal_places=2, max_digits=12, default=D('0.00'))
    
    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    _basket = None

    class Meta:
        verbose_name_plural = 'Order and item charges'
    
    def set_basket(self, basket):
        self._basket = basket
    
    def basket_charge_incl_tax(self):
        """
        Return basket total including tax
        """
        if self.free_shipping_threshold != None and \
                self._basket.total_incl_tax >= self.free_shipping_threshold:
            return D('0.00')
        
        charge = self.price_per_order
        for line in self._basket.lines.all():
            charge += line.quantity * self.price_per_item
        return charge
    
    def basket_charge_excl_tax(self):
        """
        Return basket total excluding tax.  
        
        Default implementation assumes shipping is tax free.
        """
        return self.basket_charge_incl_tax()


class WeightBased(ShippingMethod):
    upper_charge = models.DecimalField(decimal_places=2, max_digits=12, null=True)

    weight_attribute = 'weight'

    def basket_charge_incl_tax(self):
        weight = Scales(attribute=self.weight_attribute).weigh_basket(self.basket)
        band = WeightBand.get_band_for_weight(self.code, weight)
        if not band:
            if WeightBand.objects.filter(method_code=self.code).count() > 0 and self.upper_charge:
                return self.upper_charge
            else:
                return D('0.00')
        return band.charge
    
    def basket_charge_excl_tax(self):
        return D('0.00')
        
    def get_band_for_weight(self, weight):
        """
        Return the weight band for a given weight
        """
        bands = self.bands.filter(upper_limit__gte=weight).order_by('upper_limit')
        if not bands.count():
            # No band for this weight
            return None
        return bands[0]


class WeightBand(models.Model):
    """
    Represents a weight band which are used by the WeightBasedShipping method.
    """
    method = models.ForeignKey(WeightBased, related_name='bands')
    upper_limit = models.FloatField(help_text=_("""Enter upper limit of this weight band in Kg"""))
    charge = models.DecimalField(decimal_places=2, max_digits=12)
    
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

    def __unicode__(self):
        return u'Charge for weights up to %s' % (self.upper_limit,)