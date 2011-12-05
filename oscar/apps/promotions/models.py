from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models import get_model

from oscar.models.fields import ExtendedURLField

Product = get_model('catalogue', 'Product')
Item = get_model('product', 'Item')


# Linking models - these link promotions to content (eg pages, or keywords)


class LinkedPromotion(models.Model):
    
    # We use generic foreign key to link to a promotion model
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    position = models.CharField(_("Position"), max_length=100, help_text="Position on page")
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
        return reverse('promotions:page-click', kwargs={'page_promotion_id': self.id})
        
    
class KeywordPromotion(LinkedPromotion):
    """
    A promotion linked to a specific keyword.

    This can be used on a search results page to show promotions
    linked to a particular keyword.
    """

    keyword = models.CharField(_("Keyword"), max_length=200)
    
    # We allow an additional filter which will let search query matches
    # be restricted to different parts of the site.
    filter = models.CharField(_("Filter"), max_length=200, blank=True, null=True)

    def get_link(self):
        return reverse('promotions:keyword-click', kwargs={'keyword_promotion_id': self.id})


# Different model types for each type of promotion


class AbstractPromotion(models.Model):
    """
    Abstract base promotion that defines the interface
    that subclasses must implement.
    """
    _type = 'Promotion'
    keywords = generic.GenericRelation(KeywordPromotion)
    pages = generic.GenericRelation(PagePromotion)
    
    class Meta:
        abstract = True
    
    @property
    def type(self):
        return _(self._type)
    
    def template_name(self):
        """
        Returns the template to use to render this
        promotion.
        """
        return 'promotions/%s.html' % self.__class__.__name__.lower()
    
    def template_context(self, *args, **kwargs):
        return {}
    
    @property
    def content_type(self):
        return ContentType.objects.get_for_model(self)
    
    @property
    def num_times_used(self):
        ctype = self.content_type
        page_count = PagePromotion.objects.filter(content_type=ctype,
                                                  object_id=self.id).count()
        keyword_count = KeywordPromotion.objects.filter(content_type=ctype,
                                                        object_id=self.id).count()   
        return page_count + keyword_count                                       


class RawHTML(AbstractPromotion):
    """
    Simple promotion - just raw HTML
    """
    _type = 'Raw HTML'
    name = models.CharField(_("Name"), max_length=128)
    
    # Used to determine how to render the promotion (eg
    # if a different width container is required).
    display_type = models.CharField(_("Display type"), max_length=128, blank=True, null=True)
    body = models.TextField(_("HTML"))
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Raw HTML'
        
    def __unicode__(self):
        return self.name


class Image(AbstractPromotion):
    """
    An image promotion is simply a named image which has an optional 
    link to another part of the site (or another site).
    
    This can be used to model both banners and pods.
    """
    _type = 'Image'
    name = models.CharField(_("Name"), max_length=128)
    link_url = ExtendedURLField(blank=True, null=True, help_text="""This is 
        where this promotion links to""")
    image = models.ImageField(upload_to=settings.OSCAR_PROMOTION_FOLDER)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    
    
class MultiImage(AbstractPromotion):
    """
    A multi-image promotion is simply a collection of image promotions
    that are rendered in a specific way.  This models things like 
    rotating banners.
    """
    _type = 'Multi-image'
    name = models.CharField(_("Name"), max_length=128)
    images = models.ManyToManyField('promotions.Image', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name


class SingleProduct(AbstractPromotion):
    _type = 'Single product'
    name = models.CharField(_("Name"), max_length=128)
    product = models.ForeignKey('catalogue.Product')
    description = models.TextField(_("Description"), null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    

class AbstractProductList(AbstractPromotion):
    """
    Abstract superclass for promotions which are essentially a list
    of products.
    """
    name = models.CharField(_("Title"), max_length=255)
    description = models.TextField(null=True, blank=True)
    link_url = ExtendedURLField(blank=True, null=True)
    link_text = models.CharField(_("Link text"), max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name
        
 
class HandPickedProductList(AbstractProductList):
    """
    A hand-picked product list is a list of manually selected
    products.
    """
    _type = 'Product list'
    products = models.ManyToManyField('catalogue.Product', through='OrderedProduct', blank=True, null=True)

    def get_products(self):
        return self.products.all().order_by('%s.display_order' % OrderedProduct._meta.db_table)
    

class OrderedProduct(models.Model):
    
    list = models.ForeignKey('promotions.HandPickedProductList')
    product = models.ForeignKey('catalogue.Product')
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('display_order',)
        
        
class AutomaticProductList(AbstractProductList):
    
    _type = 'Auto-product list'
    BESTSELLING, RECENTLY_ADDED = ('Bestselling', 'RecentlyAdded')
    METHOD_CHOICES = (
        (BESTSELLING, _("Bestselling products")),
        (RECENTLY_ADDED, _("Recently added products")),
    )
    method = models.CharField(max_length=128, choices=METHOD_CHOICES)
    num_products = models.PositiveSmallIntegerField(default=4)  
    
    def get_products(self):
        if self.method == self.BESTSELLING:
            return Product.objects.all().order_by('-score')[:self.num_products]
        return Product.objects.all().order_by('-date_created')[:self.num_products]


class OrderedProductList(HandPickedProductList):
    tabbed_block = models.ForeignKey('promotions.TabbedBlock',
                                     related_name='tabs')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('display_order',)


class TabbedBlock(AbstractPromotion):

    _type = 'Tabbed block'
    name = models.CharField(_("Title"), max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

