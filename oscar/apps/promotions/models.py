from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from oscar.forms.fields import ExtendedURLField

# Settings-controlled stuff
BANNER_FOLDER = settings.OSCAR_BANNER_FOLDER
POD_FOLDER = settings.OSCAR_POD_FOLDER

# Different model types for each type of promotion


class Promotion(models.Model):
    
    class Meta:
        abstract = True
    
    def template_name(self):
        pass
    
    def template_context(self):
        return {}


class Banner(Promotion):
    
    name = models.CharField(_("Name"), max_length=128)
    link_url = ExtendedURLField(blank=True, null=True, help_text="""This is 
        where this promotion links to""")
    image = models.ImageField(upload_to=BANNER_FOLDER, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    

class Pod(Promotion):
    
    name = models.CharField(_("Name"), max_length=128)
    link_url = ExtendedURLField(blank=True, null=True, help_text="""This is 
        where this promotion links to""")
    image = models.ImageField(upload_to=BANNER_FOLDER, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name


class AbstractProductList(models.Model):
    """
    Abstract superclass for promotions which are essentially a list
    of products.
    """
    
    name = models.CharField(_("Title"), max_length=255)
    description = models.TextField(null=True, blank=True)
    link_url = ExtendedURLField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name
        
 
class HandPickedProductList(AbstractProductList):
    
    products = models.ManyToManyField('product.Item', through='OrderedProduct', blank=True, null=True)
    

class OrderedProduct(models.Model):
    
    list = models.ForeignKey('promotions.HandPickedProductList')
    product = models.ForeignKey('product.Item')
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('display_order',)
        
        
class AutomaticProductList(AbstractProductList):
    
    BESTSELLING, RECENTLY_ADDED = ('Bestselling', 'RecentlyAdded')
    METHOD_CHOICES = (
        (BESTSELLING, _("Bestselling products")),
        (RECENTLY_ADDED, _("Recently added products")),
    )
    method = models.CharField(max_length=128, choices=METHOD_CHOICES)
    num_products = models.PositiveSmallIntegerField(default=4)  


class OrderedProductList(models.Model):
    
    tabbed_block = models.ForeignKey('promotions.TabbedBlock')
    list = models.ForeignKey('promotions.HandPickedProductList')
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('display_order',)


class TabbedBlock(Promotion):

    tabs = models.ManyToManyField('promotions.HandPickedProductList', through='OrderedProductList', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    
# Linking models

TOP, LEFT, RIGHT = ('Top', 'Left', 'Right')
POSITION_CHOICES = (
    (TOP, _("Top of page")),
    (LEFT, _("Left-hand sidebar")),
    (RIGHT, _("Right-hand sidebar")),
)


class LinkedPromotion(models.Model):
    
    # We use generic foreign key to link to a promotion model
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    position = models.CharField(_("Position"), max_length=100, help_text="Position on page", choices=POSITION_CHOICES)
    display_order = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-clicks']

    def record_click(self):
        self.clicks += 1
        self.save()


class PagePromotion(LinkedPromotion):
    """
    A promotion embedded on a particular page.
    """
    page_url = ExtendedURLField(max_length=128, db_index=True)

    def __unicode__(self):
        return u"%s on %s" % (self.content_object, self.page_url)
    
    def get_link(self):
        return reverse('oscar-page-promotion-click', kwargs={'page_promotion_id': self.id})
        
    
class KeywordPromotion(LinkedPromotion):
    """
    A promotion linked to a specific keyword.

    This can be used on a search results page to show promotions
    linked to a particular keyword.
    """

    keyword = models.CharField(_("Keyword"), max_length=200)

    def get_link(self):
        return reverse('oscar-keyword-promotion-click', kwargs={'keyword_promotion_id': self.id})






