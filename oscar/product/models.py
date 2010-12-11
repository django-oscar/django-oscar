from django.db import models
from django.utils.translation import ugettext_lazy as _

class AttributeType(models.Model):
    """Defines an item attribute type"""
    name = models.CharField(_('name'), max_length=128)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class ItemType(models.Model):
    """Defines an item type"""
    name = models.CharField(_('name'), max_length=128)
    attribute_types = models.ManyToManyField('product.AttributeType', 
                                        through='product.AttributeTypeMembership',
                                        verbose_name=_('attribute types'))

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class AttributeTypeMembership(models.Model):
    REL_OPTIONAL = 'optional'
    REL_REQUIRED = 'required'
    REL_REQUIRED_BASKET = 'required_basket'
    RELATIONSHIP_CHOICES = (
        (REL_OPTIONAL, _('optional')),
        (REL_REQUIRED, _('required')),
        (REL_REQUIRED_BASKET, _('required for purchase')),
    )
    product_type = models.ForeignKey('product.ItemType')
    attribute_type = models.ForeignKey('product.AttributeType')
    relation_type = models.CharField(max_length=16, choices=RELATIONSHIP_CHOICES, 
                                        default=REL_OPTIONAL)
    
    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.item_type.name, self.attribute_type.name, 
                                  self.relation_type)
    

class Item(models.Model):
    """The base product object"""
    name = models.CharField(_('name'), max_length=255)
    partner_id = models.CharField(_('partner ID'), max_length=32)
    item_type = models.ForeignKey('product.ItemType', verbose_name=_('item type'))
    date_available = models.DateTimeField(_('date available'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']

    def __unicode__(self):
        return self.name

    def is_valid(self):
        """
        Returns true if the product is valid.

        Validity is based on whether the product has all required attribute types
        configured for the product_class it is in.

        Returns:
            A boolean if the product is valid

        #TODISCUSS: When is this run? Is it not possible to cache it on
        the model during save? This is beastly and needs rewriting. #TODO
        """
        required_attribute_names = self.item_type.attribute_types\
                .filter(attributetypemembership__relation_type=AttributeTypeMembership.REL_REQUIRED)\
                .values_list('name', flat=True)

        for attribute in self.attribute_set.all():
            if attribute.attribute_type.name in required_attribute_names:
                required_attribute_names.remove(attribute.attribute_type.name)

        return 0 == len(required_attribute_names)


class Attribute(models.Model):
    """An individual product attribute"""
    attribute_type = models.ForeignKey('product.AttributeType', 
                                        verbose_name=_('attribute type'))
    product = models.ForeignKey('product.Item', verbose_name=_('product'))
    value = models.CharField(_('value'), max_length=255)


class StockRecord(models.Model):
    """A stock keeping record"""
    # TODISCUSS: Stock control is massive, I believe it should 
    # be in a seperate app.
    product = models.ForeignKey('product.Item', verbose_name=_('product'))
    price_excl_tax = models.DecimalField(_('price exc. VAT'), max_digits=10, 
                                        decimal_places=2)
    tax = models.DecimalField(_('tax'), max_digits=10, decimal_places=2)
