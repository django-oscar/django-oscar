from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _


class AbstractProductRecord(models.Model):
    u"""
    A record of a how popular a product is.
    
    This used be auto-merchandising to display the most popular
    products.
    """
    
    product = models.OneToOneField('product.Item')
    num_views = models.PositiveIntegerField(default=0)
    num_basket_additions = models.PositiveIntegerField(default=0)
    num_purchases = models.PositiveIntegerField(default=0, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-num_purchases']
        

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
        
    