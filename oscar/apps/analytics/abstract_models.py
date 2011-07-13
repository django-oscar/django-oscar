from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _


class AbstractProductRecord(models.Model):
    u"""
    A record of a how popular a product is.
    
    This used be auto-merchandising to display the most popular
    products.
    """
    
    product = models.OneToOneField('catalogue.Product')
    
    # Data used for generating a score
    num_views = models.PositiveIntegerField(default=0)
    num_basket_additions = models.PositiveIntegerField(default=0)
    num_purchases = models.PositiveIntegerField(default=0, db_index=True)
    
    # Product score - used within search
    score = models.FloatField(default=0.00)
    
    class Meta:
        abstract = True
        ordering = ['-num_purchases']
        
    def __unicode__(self):
        return u"Record for '%s'" % self.product
        

class AbstractUserRecord(models.Model):
    u"""
    A record of a user's activity.
    """
    
    user = models.OneToOneField('auth.User')
    
    # Browsing stats
    num_product_views = models.PositiveIntegerField(default=0)
    num_basket_additions = models.PositiveIntegerField(default=0)
    
    # Order stats
    num_orders = models.PositiveIntegerField(default=0, db_index=True)
    num_order_lines = models.PositiveIntegerField(default=0, db_index=True)
    num_order_items = models.PositiveIntegerField(default=0, db_index=True)
    total_spent = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal('0.00'))
    date_last_order = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        abstract = True
        
        
class AbstractUserProductView(models.Model):
    
    user = models.ForeignKey('auth.User')
    product = models.ForeignKey('catalogue.Product')
    date_created = models.DateTimeField(auto_now_add=True)
     
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u"%s viewed '%s'" % (self.user, self.product)
             

class AbstractUserSearch(models.Model):
    
    user = models.ForeignKey('auth.User')
    query = models.CharField(_("Search term"), max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
     
    class Meta:
        abstract = True
        verbose_name_plural = _("User search queries")
        
    def __unicode__(self):
        return u"%s searched for '%s'" % (self.user, self.query)
