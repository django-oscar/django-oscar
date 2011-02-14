"""
Models for the stock and fulfillment components of an project
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractPartner(models.Model):
    u"""Fulfillment partner"""
    name = models.CharField(max_length=128)
    
    class Meta:
        verbose_name_plural = 'Fulfillment partners'
        abstract = True
        
    def __unicode__(self):
        return self.name


class AbstractStockRecord(models.Model):
    u"""
    A basic stock record.
    
    This links a product to a partner, together with price and availability
    information.  Most projects will need to subclass this object to add custom
    fields such as lead_time, report_code, min_quantity.
    """
    product = models.OneToOneField('product.Item')
    partner = models.ForeignKey('stock.Partner')
    partner_reference = models.CharField(max_length=128, blank=True)
    
    # Price info:
    # We deliberately don't store tax information to allow each project
    # to subclass this model and put its own fields for convey tax.
    price_currency = models.CharField(max_length=12, default='GBP')
    # This is the base price for calculations
    price_excl_tax = models.DecimalField(decimal_places=2, max_digits=12)
    
    # Stock level information
    num_in_stock = models.IntegerField(default=0)
    num_allocated = models.IntegerField(default=0)
    
    class Meta:
        abstract = True
    
    def decrement_num_in_stock(self, delta):
        if self.num_in_stock >= delta:
            self.num_in_stock -= delta
        self.num_allocated += delta
        self.save()
        
    # Price retrieval methods - these default to no tax being applicable
    # These are intended to be overridden.   
    
    @property
    def availability(self):
        if self.num_in_stock:
            return _("In stock (%d available)" % self.num_in_stock)
        return _("Out of stock")
    
    @property 
    def price_incl_tax(self):
        return self.price_excl_tax
    
    @property 
    def price_tax(self):
        return 0
        
    def __unicode__(self):
        if self.partner_reference:
            return "%s (%s): %s" % (self.partner.name, self.partner_reference, self.product.title)
        else:
            return "%s: %s" % (self.partner.name, self.product.title)