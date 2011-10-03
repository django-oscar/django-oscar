"""
Models of products
"""
import re
from itertools import chain
from datetime import datetime, date

from django.db import models
from django.core.validators import RegexValidator
from django.db.models import get_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from treebeard.mp_tree import MP_Node

from oscar.apps.catalogue.managers import BrowsableProductManager

ENABLE_ATTRIBUTE_BINDING = getattr(settings, 'OSCAR_ENABLE_ATTRIBUTE_BINDING', False)

class AbstractProductClass(models.Model):
    """
    Defines the options and attributes for a group of products, e.g. Books, DVDs and Toys.
    Not necessarily equivalent to top-level categories but usually will be.
    """
    name = models.CharField(_('name'), max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    
    # These are the options (set by the user when they add to basket) for this item class
    options = models.ManyToManyField('catalogue.Option', blank=True)

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name_plural = "Product classes"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug= slugify(self.name)
        super(AbstractProductClass, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class AbstractCategory(MP_Node):
    """
    Category hierarchy, top-level nodes represent departments. Uses django-treebeard.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=1024, db_index=True, editable=False)
    full_name = models.CharField(max_length=1024, db_index=True, editable=False)    
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            parent = self.get_parent()
            slug = slugify(self.name)
            if parent:
                self.slug = '%s/%s' % (parent.slug, slug)
                self.full_name = '%s > %s' % (parent.full_name, self.name)
            else:
                self.slug = slug
                self.full_name = self.name
        super(AbstractCategory, self).save(*args, **kwargs)

    def get_ancestors(self, include_self=True):
        ancestors = list(super(AbstractCategory, self).get_ancestors())
        if include_self:
            ancestors.append(self)
        return ancestors

    @models.permalink
    def get_absolute_url(self):
        return ('catalogue:category', (), {
                'category_slug': self.slug })

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name_plural = 'Categories'
        verbose_name = 'Category'


class AbstractProductCategory(models.Model):
    """
    Joining model between products and categories.
    """
    product = models.ForeignKey('catalogue.Product')
    category = models.ForeignKey('catalogue.Category')
    is_canonical = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-is_canonical']
        verbose_name_plural = 'Categories'
        

class AbstractContributorRole(models.Model):
    """
    A role that may be performed by a contributor to a product, eg Author, Actor, Director.
    """
    name = models.CharField(max_length=50)
    name_plural = models.CharField(max_length=50)
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractContributorRole, self).save(*args, **kwargs) 


class AbstractContributor(models.Model):
    """
    Represents a person or business that has contributed to a product in some way. eg an author.
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(max_length=255, unique=False)

    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractContributor, self).save(*args, **kwargs)


class AbstractProductContributor(models.Model):
    product = models.ForeignKey('catalogue.Product')
    contributor = models.ForeignKey('catalogue.Contributor')
    role = models.ForeignKey('catalogue.ContributorRole')
    
    def __unicode__(self):
        return '%s <- %s - %s' % (self.product, self.role, self.contributor)
    
    class Meta:
        abstract = True


class AbstractProduct(models.Model):
    """
    The base product object
    """
    # If an item has no parent, then it is the "canonical" or abstract version of a product
    # which essentially represents a set of products.  If a product has a parent
    # then it is a specific version of a catalogue.
    # 
    # For example, a canonical product would have a title like "Green fleece" while its 
    # children would be "Green fleece - size L".
    
    # Universal product code
    upc = models.CharField(_("UPC"), max_length=64, blank=True, null=True, db_index=True,
        help_text="""Universal Product Code (UPC) is an identifier for a product which is 
                     not specific to a particular supplier.  Eg an ISBN for a book.""")
    
    # No canonical product should have a stock record as they cannot be bought.
    parent = models.ForeignKey('self', null=True, blank=True, related_name='variants',
        help_text="""Only choose a parent product if this is a 'variant' of a canonical catalogue.  For example 
                     if this is a size 4 of a particular t-shirt.  Leave blank if this is a CANONICAL PRODUCT (ie 
                     there is only one version of this product).""")
    
    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(_('Title'), max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=False)
    description = models.TextField(_('Description'), blank=True, null=True)
    product_class = models.ForeignKey('catalogue.ProductClass', verbose_name=_('product class'), null=True,
        help_text="""Choose what type of product this is""")
    attributes = models.ManyToManyField('catalogue.ProductAttribute', through='ProductAttributeValue',
        help_text="""A product attribute is something that this product MUST have, such as a size, as specified by its class""")
    product_options = models.ManyToManyField('catalogue.Option', blank=True, 
        help_text="""Options are values that can be associated with a item when it is added to 
                     a customer's basket.  This could be something like a personalised message to be
                     printed on a T-shirt.<br/>""")
    
    related_products = models.ManyToManyField('catalogue.Product', related_name='relations', blank=True, help_text="""Related 
        items are things like different formats of the same book.  Grouping them together allows
        better linking betwen products on the site.<br/>""")
    
    # Recommended products
    recommended_products = models.ManyToManyField('catalogue.Product', through='ProductRecommendation', blank=True)
    
    # Product score
    score = models.FloatField(default=0.00, db_index=True)
    
    date_created = models.DateTimeField(auto_now_add=True)

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(auto_now=True, db_index=True)
    
    categories = models.ManyToManyField('catalogue.Category', through='ProductCategory')

    objects = models.Manager()
    browsable = BrowsableProductManager()

    # Properties

    @property
    def options(self):
        return list(chain(self.product_options.all(), self.get_product_class().options.all()))

    @property
    def is_top_level(self):
        u"""Return True if this is a parent product"""
        return self.parent_id == None
    
    @property
    def is_group(self):
        u"""Return True if this is a top level product and has more than 0 variants"""
        return self.is_top_level and self.variants.count() > 0
    
    @property
    def is_variant(self):
        u"""Return True if a product is not a top level product"""
        return not self.is_top_level

    @property
    def min_variant_price_incl_tax(self):
        u"""Return minimum variant price including tax"""
        return self._min_variant_price('price_incl_tax')
    
    @property
    def min_variant_price_excl_tax(self):
        u"""Return minimum variant price excluding tax"""
        return self._min_variant_price('price_excl_tax')

    @property
    def has_stockrecord(self):
        u"""Return True if a product has a stock record, False if not"""
        try:
            self.stockrecord
            return True
        except ObjectDoesNotExist:
            return False

    def add_category_from_breadcrumbs(self, breadcrumb):
        from oscar.apps.catalogue.utils import breadcrumbs_to_category
        category = breadcrumbs_to_category(breadcrumb)
        
        temp = models.get_model('product', 'productcategory')(category=category, product=self)
        temp.save()

    def attribute_summary(self):
        u"""Return a string of all of a product's attributes"""
        return ", ".join([attribute.__unicode__() for attribute in self.attributes.all()])

    def get_title(self):
        u"""Return a product's title or it's parent's title if it has no title"""
        title = self.__dict__.setdefault('title', '')
        if not title and self.parent_id:
            title = self.parent.title
        return title
    
    def get_product_class(self):
        u"""Return a product's item class"""
        if self.product_class:
            return self.product_class
        if self.parent.product_class:
            return self.parent.product_class
        return None

    # Helpers
    
    def _min_variant_price(self, property):
        u"""Return minimum variant price"""
        prices = []
        for variant in self.variants.all():
            if variant.has_stockrecord:
                prices.append(getattr(variant.stockrecord, property))
        if not prices:
            return None
        prices.sort()
        return prices[0]

    class Meta:
        abstract = True
        ordering = ['-date_created']

    def __unicode__(self):
        if self.is_variant:
            return u"%s (%s)" % (self.get_title(), self.attribute_summary())
        return self.get_title()
    
    @models.permalink
    def get_absolute_url(self):
        u"""Return a product's absolute url"""
        return ('catalogue:detail', (), {
            'product_slug': self.slug,
            'pk': self.id})
        
    def __init__(self, *args, **kwargs):
        super(AbstractProduct, self).__init__(*args, **kwargs)
        if ENABLE_ATTRIBUTE_BINDING:
            self.attr = ProductAttributesContainer(product=self)
    
    def save(self, *args, **kwargs):
        if self.is_top_level and not self.title:
            raise ValidationError("Canonical products must have a title")
        if not self.slug:
            self.slug = slugify(self.get_title())
        
        # Validate attributes if necessary
        if ENABLE_ATTRIBUTE_BINDING:
            self.attr.validate_attributes()
            
        # Save product
        super(AbstractProduct, self).save(*args, **kwargs)
        
        # Finally, save attributes
        if ENABLE_ATTRIBUTE_BINDING:
            self.attr.save()


class ProductRecommendation(models.Model):
    u"""
    'Through' model for product recommendations
    """
    primary = models.ForeignKey('catalogue.Product', related_name='primary_recommendations')
    recommendation = models.ForeignKey('catalogue.Product')
    ranking = models.PositiveSmallIntegerField(default=0)


class ProductAttributesContainer(object):
    """
    Stolen liberally from django-eav, but simplified to be product-specific
    """
    
    def __init__(self, product):
        self.product = product
        self.initialised = False

    def __getattr__(self, name):
        if not name.startswith('_') and not self.initialised:
            values = list(self.get_values().select_related('attribute'))
            result = None
            for v in values:
                setattr(self, v.attribute.code, v.value)
                if v.attribute.code == name:
                    result = v.value
            self.initialised = True
            if result:
                return result
        raise AttributeError((_(u"%(obj)s has no attribute named " \
                                       u"'%(attr)s'") % \
                                     {'obj': self.product.product_class, 'attr': name}))
        
    def validate_attributes(self):
        for attribute in self.get_all_attributes():
            value = getattr(self, attribute.code, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(_(u"%(attr)s attribute cannot " \
                                            u"be blank") % \
                                            {'attr': attribute.code})
            else:
                try:
                    attribute.validate_value(value)
                except ValidationError, e:
                    raise ValidationError(_(u"%(attr)s attribute %(err)s") % \
                                            {'attr': attribute.code,
                                             'err': e})
        
    def get_values(self):
        return self.product.productattributevalue_set.all()
    
    def get_value_by_attribute(self, attribute):
        return self.get_values().get(attribute=attribute)    
    
    def get_all_attributes(self):
        return self.product.product_class.attributes.all()
    
    def get_attribute_by_code(self, code):
        return self.get_all_attributes().get(code=code)
    
    def __iter__(self):
        return iter(self.get_values())
    
    def save(self):
        for attribute in self.get_all_attributes():
            if hasattr(self, attribute.code):
                value = getattr(self, attribute.code)
                attribute.save_value(self.product, value)


class AbstractProductAttribute(models.Model):
    
    TYPE_CHOICES = (
        ("text", "Text"), 
        ("integer", "Integer"),
        ("boolean", "True / False"), 
        ("float", "Float"), 
        ("richtext", "Rich Text"), 
        ("date", "Date"), 
        ("option", "Option"),
        ("entity", "Entity"),
    )
    
    """
    Defines an attribute for a product class. (For example, number_of_pages for a 'book' class)
    """
    product_class = models.ForeignKey('catalogue.ProductClass', related_name='attributes', blank=True, null=True)
    name = models.CharField(_('name'), max_length=128)
    code = models.SlugField(_('code'), max_length=128, validators=[RegexValidator(regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$', message="Code must match ^[a-zA-Z_][0-9a-zA-Z_]*$")])
    type = models.CharField(choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0], max_length=20)
    option_group = models.ForeignKey('catalogue.AttributeOptionGroup', blank=True, null=True, help_text='Select an option group if using type "Option"')
    entity_type = models.ForeignKey('catalogue.AttributeEntityType', blank=True, null=True, help_text='Select an entity type if using type "Entity"')
    required = models.BooleanField(default=False)

    class Meta:
        abstract = True 
        ordering = ['code']

    def _validate_text(self, value):
        if not (type(value) == unicode or type(value) == str):
            raise ValidationError(_(u"Must be str or unicode"))

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_(u"Must be a float"))

    def _validate_int(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_(u"Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_(u"Must be a date or datetime"))

    def _validate_bool(self, value):
        if not type(value) == bool:
            raise ValidationError(_(u"Must be a boolean"))

    def _validate_entity(self, value):
        if not isinstance(value, get_model('catalogue', 'AttributeEntity')):
            raise ValidationError(_(u"Must be an AttributeEntity model object instance"))
        if not value.pk:
            raise ValidationError(_(u"Model has not been saved yet"))
        if value.type != self.entity_type:
            raise ValidationError(_(u"Entity must be of type %s" % self.entity_type.name))

    def _validate_option(self, value):
        if not isinstance(value, get_model('catalogue', 'AttributeOption')):
            raise ValidationError(_(u"Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_(u"AttributeOption has not been saved yet"))
        valid_values = self.option_group.options.values_list('option', flat=True)
        if value not in valid_values:
            raise ValidationError(_(u"%(enum)s is not a valid choice "
                                        u"for %(attr)s") % \
                                       {'enum': value, 'attr': self})        


    def get_validator(self):
        DATATYPE_VALIDATORS = {
            'text': self._validate_text,
            'integer': self._validate_int,
            'boolean': self._validate_bool,
            'float': self._validate_float,
            'richtext': self._validate_text,
            'date': self._validate_date,
            'entity': self._validate_entity,
            'option': self._validate_option,
        }

        return DATATYPE_VALIDATORS[self.type]     

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(AbstractProductAttribute, self).save(*args, **kwargs)
        
    def save_value(self, product, value):
        try:
            value_obj = product.productattributevalue_set.get(attribute=self)
        except get_model('catalogue', 'ProductAttributeValue').DoesNotExist:
            if value == None or value == '':
                return
            value_obj = get_model('catalogue', 'ProductAttributeValue').objects.create(product=product, attribute=self)
        if value == None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()
    
    def validate_value(self, value):
        self.get_validator()(value)
        
    def is_value_valid(self, value):
        """
        Check whether the passed value is valid for this attribute
        """
        if self.type == 'option':
            valid_values = self.option_group.options.values_list('option', flat=True)
            return value in valid_values
        return True


class AbstractProductAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between catalogue.Product
    and catalogue.ProductAttribute.  
    This specifies the value of the attribute for a particular product
    
    For example: number_of_pages = 295
    """
    attribute = models.ForeignKey('catalogue.ProductAttribute')
    product = models.ForeignKey('catalogue.Product')
    value_text = models.CharField(max_length=255, blank=True, null=True)
    value_integer = models.IntegerField(blank=True, null=True)
    value_boolean = models.BooleanField(blank=True)
    value_float = models.FloatField(blank=True, null=True)
    value_richtext = models.TextField(blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)
    value_option = models.ForeignKey('catalogue.AttributeOption', blank=True, null=True)
    value_entity = models.ForeignKey('catalogue.AttributeEntity', blank=True, null=True)
    
    def _get_value(self):
        return getattr(self, 'value_%s' % self.attribute.type)
    
    def _set_value(self, new_value):
        if self.attribute.type == 'option' and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(option=new_value)
        setattr(self, 'value_%s' % self.attribute.type, new_value)
    
    value = property(_get_value, _set_value)
    
    class Meta:
        abstract = True 
        
    def __unicode__(self):
        return u"%s: %s" % (self.attribute.name, self.value)
    
    
class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an 
    attribute type
    For example, Language
    """
    name = models.CharField(max_length=128)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = True


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    group = models.ForeignKey('catalogue.AttributeOptionGroup', related_name='options')
    option = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.option
    
    class Meta:
        abstract = True
    
    
class AbstractAttributeEntity(models.Model):
    """
    Provides an attribute type to enable relationships with other models
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(max_length=255, unique=False, blank=True)
    type = models.ForeignKey('catalogue.AttributeEntityType', related_name='entities')

    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = True
        verbose_name_plural = 'Attribute entities'
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractAttributeEntity, self).save(*args, **kwargs)


class AbstractAttributeEntityType(models.Model):
    """
    Provides the name of the model involved in an entity relationship
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(max_length=255, unique=False, blank=True)
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractAttributeEntityType, self).save(*args, **kwargs)
    
    
class AbstractOption(models.Model):
    u"""
    An option that can be selected for a particular item when the product
    is added to the basket.  
    
    Eg a list ID for an SMS message send, or a personalised message to 
    print on a T-shirt.  
    
    This is not the same as an attribute as options do not have a fixed value for 
    a particular item - options, they need to be specified by the customer.
    """
    name = models.CharField(_('name'), max_length=128)
    code = models.SlugField(_('code'), max_length=128)
    
    REQUIRED, OPTIONAL = ('Required', 'Optional')
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    type = models.CharField(_("Status"), max_length=128, default=REQUIRED, choices=TYPE_CHOICES)
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractOption, self).save(*args, **kwargs)


class AbstractProductImage(models.Model):
    u"""An image of a product"""
    product = models.ForeignKey('catalogue.Product', related_name='images')
    
    original = models.ImageField(upload_to=settings.OSCAR_IMAGE_FOLDER)
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

