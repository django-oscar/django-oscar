"""
Core address objects
"""
import zlib

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify


class AbstractMethod(models.Model):
    u"""
    Shipping method
    """
    code = models.CharField(max_length=128)
    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"), blank=True)
    price_currency = models.CharField(max_length=12, default='GBP')
    price_per_order = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    price_per_item = models.DecimalField(decimal_places=2, max_digits=12, default=0)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractMethod, self).save(*args, **kwargs)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name