"""
Models of products
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractItemClass(models.Model):
    """
    Defines an item type (equivqlent to Taoshop's MediaType).
    """
    name = models.CharField(_('name'), max_length=128)

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name_plural = "Item classes"

    def __unicode__(self):
        return self.name


class AbstractItem(models.Model):
    """
    The base product object
    """
    # If an item has no parent, then it is the "canonical" or abstract version of a product
    # which essentially represents a set of products.  If a product has a parent
    # then it is a specific version of a product.
    # 
    # For example, a canonical product would have a title like "Green fleece" while its 
    # children would be "Green fleece - size L".
    
    # Universal product code
    upc = models.CharField(max_length=64, blank=True)
    # No canonical product should have a stock record as they cannot be bought.
    parent = models.ForeignKey('self', null=True, blank=True,
        help_text="""Only choose a parent product if this is a 'variant' of a canonical product.  For example 
                     if this is a size 4 of a particular t-shirt.  Leave blank if this is a CANONICAL PRODUCT (ie 
                     there is only one version of this product).""")
    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(_('title'), max_length=255, blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)
    item_class = models.ForeignKey('product.ItemClass', verbose_name=_('item class'), null=True,
        help_text="""Choose what type of product this is""")
    attribute_types = models.ManyToManyField('product.AttributeType', through='ItemAttributeValue')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True, null=True, default=None)

    def is_canonical(self):
        return self.parent == None

    def get_attribute_summary(self):
        return ", ".join([attribute.__unicode__() for attribute in self.attributes.all()])

    # Set title as a property so we can forward the method call to the parent product
    def _get_title(self):
        title = self.__dict__.setdefault('title', '')
        if not title and self.parent_id:
            title = self.parent.title
        return title
    def _set_title(self, title):
        self.__dict__['title'] = title
    title = property(_get_title, _set_title)
    
    # Set item_class as a property so we can forward the method call to the parent product
    def _get_item_class(self):
        item_class = self.__dict__.setdefault('item_class', None)
        if not item_class and self.parent_id:
            item_class = self.parent.item_class
        return item_class
    def _set_item_class(self, item_class):
        self.__dict__['item_class'] = item_class
    item_class = property(_get_item_class, _set_item_class)

    class Meta:
        abstract = True
        ordering = ['-date_created']

    def __unicode__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_canonical() and not self.title:
            from django.core.exceptions import ValidationError
            raise ValidationError("Canonical products must have a title")
        super(AbstractItem, self).save(*args, **kwargs)


class AbstractAttributeType(models.Model):
    """
    Defines an attribute. (Eg. size)
    """
    type = models.CharField(_('type'), max_length=128)
    has_choices = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ['type']

    def __unicode__(self):
        return self.type


class AbstractAttributeValueOption(models.Model):
    """
    Defines an attribute value choice (Eg: S,M,L,XL for a size attribute type)
    """
    type = models.ForeignKey('product.AttributeType', related_name='options')
    value = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s = %s" % (self.type, self.value)


class AbstractItemAttributeValue(models.Model):
    """
    A specific attribute value for an item.
    
    Eg: size = L
    """
    product = models.ForeignKey('product.Item', related_name='attributes')
    attribute = models.ForeignKey('product.AttributeType')
    value = models.CharField(max_length=255)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return "%s: %s" % (self.attribute.type, self.value)