from django.db import models
from django.utils.translation import ugettext_lazy as _

class AbstractAttributeType(models.Model):
    """
    Defines an item attribute type
    """
    name = models.CharField(_('name'), max_length=128)

    class Meta:
        abstract = True
        ordering = ['name']

    def __unicode__(self):
        return self.name


class AbstractItemType(models.Model):
    """
    Defines an item type (equivqlent to Taoshop's MediaType).
    
    An item type is defined by a set of attribute types which can 
    be REQUIRED, OPTIONAL. 
    
    Eg. An ItemType of Jumper would have two Attributes (both REQUIRED):
    Size and Colour.  Both of these attributes have to be set for the 
    item to be valid.
    """
    name = models.CharField(_('name'), max_length=128)
    attribute_types = models.ManyToManyField('product.AttributeType', 
                                             through='product.AttributeTypeMembership',
                                             verbose_name=_('attribute types'))

    class Meta:
        abstract = True
        ordering = ['name']

    def __unicode__(self):
        return self.name


class AbstractAttributeTypeMembership(models.Model):
    OPTIONAL, REQUIRED  = ('optional', 'required')
    RELATIONSHIP_CHOICES = (
        (OPTIONAL, _('optional')),
        (REQUIRED, _('required')),
    )
    product_type = models.ForeignKey('product.ItemType')
    attribute_type = models.ForeignKey('product.AttributeType')
    relation_type = models.CharField(max_length=16, 
                                     choices=RELATIONSHIP_CHOICES, 
                                     default=REQUIRED)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.item_type.name, 
                                   self.attribute_type.name, 
                                   self.relation_type)
    

class AbstractItem(models.Model):
    """
    The base product object
    """
    title = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    item_type = models.ForeignKey('product.ItemType', verbose_name=_('item type'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-date_created']

    def __unicode__(self):
        return self.title

    def get_attributes_summary(self):
        return self.attributes.all()

    def has_required_attributes(self):
        """
        Returns true if the product is properly configured..

        Validity is based on whether the product has all required attribute types
        configured for the product_class it is in.

        #TODISCUSS: When is this run? Is it not possible to cache it on
        the model during save? This is beastly and needs rewriting. #TODO
        """
        required_attribute_names = self.item_type.attribute_types\
                .filter(attributetypemembership__relation_type=AbstractAttributeTypeMembership.REL_REQUIRED)\
                .values_list('name', flat=True)

        for attribute in self.attributes.all():
            if attribute.attribute_type.name in required_attribute_names:
                required_attribute_names.remove(attribute.attribute_type.name)

        return 0 == len(required_attribute_names)


class AbstractAttribute(models.Model):
    """
    An individual product attribute
    """
    attribute_type = models.ForeignKey('product.AttributeType', 
                                        verbose_name=_('attribute type'),
                                        related_name='attributes'
                                        )
    product = models.ForeignKey('product.Item', verbose_name=_('product'))
    value = models.CharField(_('value'), max_length=255)
    
    class Meta:
        abstract = True
