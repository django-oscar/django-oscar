from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.conf import settings

from oscar.apps.shipping.methods import ShippingMethod


class AbstractOrderAndItemLevelChargeMethod(models.Model, ShippingMethod):
    u"""
    Standard shipping method
    
    This method has two components: 
    * a charge per order
    * a charge per item
    
    Many sites use shipping logic which fits into this system.  However, for more
    complex shipping logic, a custom shipping method object will need to be provided
    that subclasses ShippingMethod.
    """
    code = models.CharField(max_length=128, unique=True)
    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"), blank=True)
    price_currency = models.CharField(max_length=12, default=settings.OSCAR_DEFAULT_CURRENCY)
    price_per_order = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    price_per_item = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    
    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    
    _basket = None
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractOrderAndItemLevelChargeMethod, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name
    
    def set_basket(self, basket):
        self._basket = basket
    
    def basket_charge_incl_tax(self):
        u"""
        Return basket total including tax
        """
        if self.free_shipping_threshold != None and self._basket.total_incl_tax >= self.free_shipping_threshold:
            return Decimal('0.00')
        
        charge = self.price_per_order
        for line in self._basket.lines.all():
            charge += line.quantity * self.price_per_item
        return charge
    
    def basket_charge_excl_tax(self):
        u"""
        Return basket total excluding tax.  
        
        Default implementation assumes shipping is tax free.
        """
        return self.basket_charge_incl_tax()