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
    #
    # No canonical product should have a stock record as they cannot be bought.
    parent = models.ForeignKey('self', blank=True, null=True)
    title = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    item_class = models.ForeignKey('product.ItemClass', verbose_name=_('item class'))
    attribute_types = models.ManyToManyField('product.AttributeType', through='ItemAttributeValue')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def is_canonical(self):
        return self.parent == None

    def get_attribute_summary(self):
        return ", ".join([attribute.__unicode__() for attribute in self.attributes.all()])

    class Meta:
        abstract = True
        ordering = ['-date_created']

    def __unicode__(self):
        return self.title

class AbstractAttributeType(models.Model):
    """
    Defines an attribute. (Eg. size)
    """
    type = models.CharField(_('type'), max_length=128)

    class Meta:
        abstract = True
        ordering = ['type']

    def __unicode__(self):
        return self.type

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