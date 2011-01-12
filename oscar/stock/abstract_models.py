"""
Models for the stock and fulfillment components of an project
"""
from django.db import models

class AbstractPartner(models.Model):
    """
    Fulfillment partner
    """
    name = models.CharField(max_length=128)
    
    class Meta:
        verbose_name_plural = 'Fulfillment partners'
        abstract = True
        
    def __unicode__(self):
        return self.name

class AbstractStockRecord(models.Model):
    """
    A basic stock record.
    
    This links a product to a partner, together with price and availability
    information.  Most projects will need to subclass this object to add custom
    fields such as lead_time, report_code, min_quantity.
    """
    product = models.OneToOneField('product.Item')
    partner = models.ForeignKey('stock.Partner')
    partner_reference = models.CharField(max_length=128, blank=True, null=True)
    price_incl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    num_in_stock = models.IntegerField()
    num_allocated = models.IntegerField()
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        if self.partner_reference:
            return "%s (%s): %s" % (self.partner.name, self.partner_reference, self.product.title)
        else:
            return "%s: %s" % (self.partner.name, self.product.title)