"""
Abstract models for product images
"""

from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings

try:
    FULLSIZE_FOLDER = settings.OSCAR_FULLSIZE_IMAGE_FOLDER
except AttributeError: 
    FULLSIZE_FOLDER = 'images/products-fullsize/%Y/%m/'

try:
    THUMBS_FOLDER = settings.OSCAR_THUMBS_IMAGE_FOLDER
except AttributeError: 
    THUMBS_FOLDER = 'images/products-thumbs/%Y/%m/'



class AbstractImage(models.Model):
    u"""An image of a product"""
    product = models.ForeignKey('product.Item', related_name='images')
    
    # Namespacing path with app name to avoid clashes with other apps
    fullsize = models.ImageField(upload_to=FULLSIZE_FOLDER)
    thumbnail = models.ImageField(upload_to=THUMBS_FOLDER)
    
    # Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def is_primary(self):
        u"""Return bool if image display order is 0"""
        return self.display_order == 0
    
    class Meta:
        abstract = True
        unique_together = ("product", "display_order")
        ordering = ["display_order"]

    def __unicode__(self):
        return u"Image of '%s'" % self.product

