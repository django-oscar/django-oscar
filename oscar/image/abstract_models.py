"""
Abstract models for product images
"""

from django.db import models
from django.utils.translation import ugettext as _


class AbstractImage(models.Model):
    u"""An image of a product"""
    product = models.ForeignKey('product.Item', related_name='images')
    # Namespacing path with app name to avoid clashes with other apps
    path_to_original = models.ImageField(upload_to='oscar/product-images/%Y/%m/')
    path_to_thumbnail = models.ImageField(upload_to='oscar/product-images/%Y/%m/')
    # Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    def is_primary(self):
        u"""Return bool if image display order is 0"""
        return self.display_order == 0
    
    class Meta:
        abstract = True

    def __unicode__(self):
        return u"Image of '%s'" % self.product

