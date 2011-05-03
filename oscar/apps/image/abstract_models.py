"""
Abstract models for product images
"""

from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings

FOLDER = settings.OSCAR_IMAGE_FOLDER

class AbstractImage(models.Model):
    u"""An image of a product"""
    product = models.ForeignKey('product.Item', related_name='images')
    
    original = models.ImageField(upload_to=FOLDER)
    caption = models.CharField(_("Caption"), max_length=200, blank=True, null=True)
    
    # Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(default=0, help_text="""An image with a display order of
       zero will be the primary image for a product""")
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        unique_together = ("product", "display_order")
        ordering = ["display_order"]

    def __unicode__(self):
        return u"Image of '%s'" % self.product

    def is_primary(self):
        u"""Return bool if image display order is 0"""
        return self.display_order == 0

    def resized_image_url(self, width=None, height=None, **kwargs):
        return self.original.url

    def fullsize_url(self):
        u"""
        Returns the URL path for this image.  This is intended
        to be overridden in subclasses that want to serve
        images in a specific way.
        """
        return self.resized_image_url()
    
    def thumbnail_url(self):
        return self.resized_image_url()