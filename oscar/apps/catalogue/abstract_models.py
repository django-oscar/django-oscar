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

from oscar.core.loading import get_class
BrowsableProductManager = get_class('catalogue.managers',
                                    'BrowsableProductManager')


class AbstractProductClass(models.Model):
    """
    Defines the options and attributes for a group of products, e.g. Books,
    DVDs and Toys.

    Not necessarily equivalent to top-level categories but usually will be.
    """
    name = models.CharField(_('Name'), max_length=128)
    slug = models.SlugField(_('Slug'), max_length=128, unique=True)

    # Some product type don't require shipping (eg digital products) - we use
    # this field to take some shortcuts in the checkout.
    requires_shipping = models.BooleanField(_("Requires shipping?"),
                                            default=True)

    # Digital products generally don't require their stock levels to be
    # tracked.
    track_stock = models.BooleanField(_("Track stock levels?"), default=True)

    # These are the options (set by the user when they add to basket) for this
    # item class.  For instance, a product class of "SMS message" would always
    # require a message to be specified before it could be bought.
    options = models.ManyToManyField('catalogue.Option', blank=True,
                                     verbose_name=_("Options"))

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _("Product Class")
        verbose_name_plural = _("Product Classes")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(AbstractProductClass, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class AbstractCategory(MP_Node):
    """
    A product category.

    Uses django-treebeard.
    """
    name = models.CharField(_('Name'), max_length=255, db_index=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    image = models.ImageField(_('Image'), upload_to='categories', blank=True,
                              null=True)
    slug = models.SlugField(_('Slug'), max_length=1024, db_index=True,
                            editable=False)
    full_name = models.CharField(_('Full Name'), max_length=1024,
                                 db_index=True, editable=False)

    _slug_separator = '/'
    _full_name_separator = ' > '

    def __unicode__(self):
        return self.full_name

    def save(self, update_slugs=True, *args, **kwargs):
        if update_slugs:
            parent = self.get_parent()
            slug = slugify(self.name)
            if parent:
                self.slug = '%s%s%s' % (parent.slug,
                                        self._slug_separator, slug)
                self.full_name = '%s%s%s' % (parent.full_name,
                                             self._full_name_separator,
                                             self.name)
            else:
                self.slug = slug
                self.full_name = self.name

        # Enforce slug uniqueness here as MySQL can't handle a unique index on
        # the slug field
        try:
            match = self.__class__.objects.get(slug=self.slug)
        except self.__class__.DoesNotExist:
            pass
        else:
            if match.id != self.id:
                raise ValidationError(
                    _("A category with slug '%(slug)s' already exists") % {
                        'slug': self.slug})
        super(AbstractCategory, self).save(*args, **kwargs)

    def move(self, target, pos=None):
        super(AbstractCategory, self).move(target, pos)

        reloaded_self = self.__class__.objects.get(pk=self.pk)
        subtree = self.__class__.get_tree(parent=reloaded_self)
        if subtree:
            slug_parts = []
            name_parts = []
            curr_depth = 0
            parent = reloaded_self.get_parent()
            if parent:
                slug_parts = [parent.slug]
                name_parts = [parent.full_name]
                curr_depth = parent.depth
            self.__class__.update_subtree_properties(
                list(subtree), slug_parts, name_parts, curr_depth=curr_depth)

    @classmethod
    def update_subtree_properties(cls, nodes, slug_parts, name_parts,
                                  curr_depth):
        """
        Update slugs and full_names of children in a subtree.
        Assumes nodes were originally in DFS order.
        """
        if nodes == []:
            return

        node = nodes[0]
        if node.depth > curr_depth:
            slug = slugify(node.name)
            slug_parts.append(slug)
            name_parts.append(node.name)

            node.slug = cls._slug_separator.join(slug_parts)
            node.full_name = cls._full_name_separator.join(name_parts)
            node.save(update_slugs=False)
            curr_depth += 1
            nodes = nodes[1:]

        else:
            slug_parts = slug_parts[:-1]
            name_parts = name_parts[:-1]
            curr_depth -= 1

        cls.update_subtree_properties(
            nodes, slug_parts, name_parts, curr_depth)

    def get_ancestors(self, include_self=True):
        ancestors = list(super(AbstractCategory, self).get_ancestors())
        if include_self:
            ancestors.append(self)
        return ancestors

    @models.permalink
    def get_absolute_url(self):
        return ('catalogue:category', (), {
                'category_slug': self.slug})

    class Meta:
        abstract = True
        ordering = ['full_name']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def has_children(self):
        return self.get_num_children() > 0

    def get_num_children(self):
        return self.get_children().count()


class AbstractProductCategory(models.Model):
    """
    Joining model between products and categories.
    """
    product = models.ForeignKey('catalogue.Product', verbose_name=_("Product"))
    category = models.ForeignKey('catalogue.Category',
                                 verbose_name=_("Category"))
    is_canonical = models.BooleanField(_('Is Cannonical'), default=False,
                                       db_index=True)

    class Meta:
        abstract = True
        ordering = ['-is_canonical']
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')

    def __unicode__(self):
        return u"<productcategory for product '%s'>" % self.product


class AbstractContributorRole(models.Model):
    """
    A role that may be performed by a contributor to a product, eg Author,
    Actor, Director.
    """
    name = models.CharField(_('Name'), max_length=50)
    name_plural = models.CharField(_('Name Plural'), max_length=50)
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _('Contributor Role')
        verbose_name_plural = _('Contributor Roles')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractContributorRole, self).save(*args, **kwargs)


class AbstractContributor(models.Model):
    """
    Represents a person or business that has contributed to a product in some
    way. eg an author.
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=False)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _('Contributor')
        verbose_name_plural = _('Contributors')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractContributor, self).save(*args, **kwargs)


class AbstractProductContributor(models.Model):
    product = models.ForeignKey('catalogue.Product', verbose_name=_("Product"))
    contributor = models.ForeignKey('catalogue.Contributor',
                                    verbose_name=_("Contributor"))
    role = models.ForeignKey('catalogue.ContributorRole', blank=True,
                             null=True, verbose_name=_("Contributor Role"))

    def __unicode__(self):
        return '%s <- %s - %s' % (self.product, self.role, self.contributor)

    class Meta:
        abstract = True
        verbose_name = _('Product Contributor')
        verbose_name_plural = _('Product Contributors')


class AbstractProduct(models.Model):
    """
    The base product object
    """
    # If an item has no parent, then it is the "canonical" or abstract version
    # of a product which essentially represents a set of products.  If a
    # product has a parent then it is a specific version of a catalogue.
    #
    # For example, a canonical product would have a title like "Green fleece"
    # while its children would be "Green fleece - size L".

    # Universal product code
    upc = models.CharField(_("UPC"), max_length=64, blank=True, null=True,
                           unique=True,
        help_text=_("Universal Product Code (UPC) is an identifier for "
                    "a product which is not specific to a particular "
                    " supplier. Eg an ISBN for a book."))

    # No canonical product should have a stock record as they cannot be bought.
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='variants',
                               verbose_name=_("Parent"),
        help_text=_("Only choose a parent product if this is a 'variant' of "
                    "a canonical catalogue.  For example if this is a size "
                    "4 of a particular t-shirt.  Leave blank if this is a "
                    "CANONICAL PRODUCT (ie there is only one version of this "
                    "product)."))

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(_('Title'), max_length=255, blank=True, null=True)
    slug = models.SlugField(_('Slug'), max_length=255, unique=False)
    description = models.TextField(_('Description'), blank=True, null=True)

    # Use this field to indicate if the product is inactive or awaiting
    # approval
    status = models.CharField(_('Status'), max_length=128, blank=True,
                              null=True, db_index=True)
    product_class = models.ForeignKey(
        'catalogue.ProductClass', verbose_name=_('Product Class'), null=True,
        help_text=_("""Choose what type of product this is"""))
    attributes = models.ManyToManyField(
        'catalogue.ProductAttribute',
        through='ProductAttributeValue',
        verbose_name=_("Attributes"),
        help_text=_("A product attribute is something that this product MUST "
                    "have, such as a size, as specified by its class"))
    product_options = models.ManyToManyField(
        'catalogue.Option', blank=True, verbose_name=_("Product Options"),
        help_text=_("Options are values that can be associated with a item "
                    "when it is added to a customer's basket.  This could be "
                    "something like a personalised message to be printed on "
                    "a T-shirt."))

    related_products = models.ManyToManyField(
        'catalogue.Product', related_name='relations', blank=True,
        verbose_name=_("Related Products"),
        help_text=_("Related items are things like different formats of the "
                    "same book.  Grouping them together allows better linking "
                    "betwen products on the site."))

    # Recommended products
    recommended_products = models.ManyToManyField(
        'catalogue.Product', through='ProductRecommendation', blank=True,
        verbose_name=_("Recommended Products"))

    # Product score
    score = models.FloatField(_('Score'), default=0.00, db_index=True)

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True,
                                        db_index=True)

    categories = models.ManyToManyField(
        'catalogue.Category', through='ProductCategory',
        verbose_name=_("Categories"))

    is_discountable = models.BooleanField(_("Is Discountable"), default=True)

    objects = models.Manager()
    browsable = BrowsableProductManager()

    # Properties

    @property
    def options(self):
        pclass = self.get_product_class()
        if pclass:
            return list(chain(self.product_options.all(),
                              self.get_product_class().options.all()))
        return self.product_options.all()

    @property
    def is_top_level(self):
        """
        Test if this product is a parent (who may or may not have children)
        """
        return self.parent_id is None

    @property
    def is_group(self):
        """
        Test if this is a top level product and has more than 0 variants
        """
        # use len() instead of count() in this specific instance
        # as variants are highly likely to be used after this
        # which reduces the amount of SQL queries required
        return self.is_top_level and len(self.variants.all()) > 0

    @property
    def is_variant(self):
        """Return True if a product is not a top level product"""
        return not self.is_top_level

    @property
    def is_shipping_required(self):
        return self.product_class.requires_shipping

    @property
    def is_available_to_buy(self):
        """
        Test whether to show an add-to-basket button for this product
        """
        if self.is_group:
            for variant in self.variants.select_related('stockrecord').all():
                if variant.is_available_to_buy:
                    return True
            return False
        return self.has_stockrecord and self.stockrecord.is_available_to_buy

    @property
    def min_variant_price_incl_tax(self):
        """Return minimum variant price including tax"""
        return self._min_variant_price('price_incl_tax')

    @property
    def min_variant_price_excl_tax(self):
        """Return minimum variant price excluding tax"""
        return self._min_variant_price('price_excl_tax')

    @property
    def has_stockrecord(self):
        """Return True if a product has a stock record, False if not"""
        try:
            self.stockrecord
            return True
        except ObjectDoesNotExist:
            return False

    def is_purchase_permitted(self, user, quantity):
        """
        Test whether this product can be bought by the passed user.
        """
        if not self.has_stockrecord:
            return False, _("No stock available")
        return self.stockrecord.is_purchase_permitted(user, quantity)

    def add_category_from_breadcrumbs(self, breadcrumb):
        from oscar.apps.catalogue.categories import create_from_breadcrumbs
        category = create_from_breadcrumbs(breadcrumb)

        temp = get_model('catalogue', 'ProductCategory')(
            category=category, product=self)
        temp.save()
    add_category_from_breadcrumbs.alters_data = True

    def attribute_summary(self):
        u"""Return a string of all of a product's attributes"""
        return ", ".join([
            attribute.__unicode__() for attribute in self.attributes.all()])

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title

    def get_product_class(self):
        """
        Return a product's item class
        """
        if self.product_class:
            return self.product_class
        if self.parent and self.parent.product_class:
            return self.parent.product_class
        return None

    def primary_image(self):
        images = self.images.all()
        if images.count():
            return images[0]
        return {
            'original': MissingProductImage(),
            'caption': '',
            'is_missing': True}

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
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

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
        self.attr = ProductAttributesContainer(product=self)

    def save(self, *args, **kwargs):
        if self.is_top_level and not self.title:
            raise ValidationError(_("Canonical products must have a title"))
        if not self.slug:
            self.slug = slugify(self.get_title())

        # Validate attributes if necessary
        self.attr.validate_attributes()

        # Save product
        super(AbstractProduct, self).save(*args, **kwargs)

        # Finally, save attributes
        self.attr.save()


class ProductRecommendation(models.Model):
    """
    'Through' model for product recommendations
    """
    primary = models.ForeignKey(
        'catalogue.Product', related_name='primary_recommendations',
        verbose_name=_("Primary Product"))
    recommendation = models.ForeignKey(
        'catalogue.Product', verbose_name=_("Recommended Product"))
    ranking = models.PositiveSmallIntegerField(_('Ranking'), default=0)

    class Meta:
        verbose_name = _('Product Recommendation')
        verbose_name_plural = _('Product Recomendations')


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
            return result
        raise AttributeError(
            _("%(obj)s has no attribute named '%(attr)s'") % {
                'obj': self.product.product_class, 'attr': name})

    def validate_attributes(self):
        for attribute in self.get_all_attributes():
            value = getattr(self, attribute.code, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(_("%(attr)s attribute cannot " \
                                            "be blank") % \
                                            {'attr': attribute.code})
            else:
                try:
                    attribute.validate_value(value)
                except ValidationError, e:
                    raise ValidationError(_("%(attr)s attribute %(err)s") % \
                                            {'attr': attribute.code,
                                             'err': e})

    def get_values(self):
        return self.product.attribute_values.all()

    def get_value_by_attribute(self, attribute):
        return self.get_values().get(attribute=attribute)

    def get_all_attributes(self):
        return self.product.get_product_class().attributes.all()

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
    """
    Defines an attribute for a product class. (For example, number_of_pages for
    a 'book' class)
    """

    TYPE_CHOICES = (
        ("text", _("Text")),
        ("integer", _("Integer")),
        ("boolean", _("True / False")),
        ("float", _("Float")),
        ("richtext", _("Rich Text")),
        ("date", _("Date")),
        ("option", _("Option")),
        ("entity", _("Entity")))
    product_class = models.ForeignKey(
        'catalogue.ProductClass', related_name='attributes', blank=True,
        null=True, verbose_name=_("Product Class"))
    name = models.CharField(_('Name'), max_length=128)
    code = models.SlugField(
        _('Code'), max_length=128,
        validators=[RegexValidator(regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
        message=_("Code must match ^[a-zA-Z_][0-9a-zA-Z_]*$"))])
    type = models.CharField(
        choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))
    option_group = models.ForeignKey(
        'catalogue.AttributeOptionGroup', blank=True, null=True,
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option"'))
    entity_type = models.ForeignKey(
        'catalogue.AttributeEntityType', blank=True, null=True,
        verbose_name=_("Entity Type"),
        help_text=_('Select an entity type if using type "Entity"'))
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        ordering = ['code']
        verbose_name = _('Product Attribute')
        verbose_name_plural = _('Product Attributes')

    def _validate_text(self, value):
        if not (type(value) == unicode or type(value) == str):
            raise ValidationError(_("Must be str or unicode"))

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_int(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_bool(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_entity(self, value):
        if not isinstance(value, get_model('catalogue', 'AttributeEntity')):
            raise ValidationError(
                _("Must be an AttributeEntity model object instance"))
        if not value.pk:
            raise ValidationError(_("Model has not been saved yet"))
        if value.type != self.entity_type:
            raise ValidationError(
                _("Entity must be of type %s" % self.entity_type.name))

    def _validate_option(self, value):
        if not isinstance(value, get_model('catalogue', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))
        valid_values = self.option_group.options.values_list('option',
                                                             flat=True)
        if value.option not in valid_values:
            raise ValidationError(_("%(enum)s is not a valid choice "
                                        "for %(attr)s") % \
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
            value_obj = product.attribute_values.get(attribute=self)
        except get_model('catalogue', 'ProductAttributeValue').DoesNotExist:
            if value == None or value == '':
                return
            model = get_model('catalogue', 'ProductAttributeValue')
            value_obj = model.objects.create(product=product, attribute=self)
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
            valid_values = self.option_group.options.values_list('option',
                                                                 flat=True)
            return value in valid_values
        return True


class AbstractProductAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between catalogue.Product
    and catalogue.ProductAttribute.
    This specifies the value of the attribute for a particular product

    For example: number_of_pages = 295
    """
    attribute = models.ForeignKey('catalogue.ProductAttribute',
                                  verbose_name=_("Attribute"))
    product = models.ForeignKey(
        'catalogue.Product', related_name='attribute_values',
        verbose_name=_("Product"))
    value_text = models.CharField(
        _('Text'), max_length=255, blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.BooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
    value_option = models.ForeignKey(
        'catalogue.AttributeOption', blank=True, null=True,
        verbose_name=_("Value Option"))
    value_entity = models.ForeignKey(
        'catalogue.AttributeEntity', blank=True, null=True,
        verbose_name=_("Value Entity"))

    def _get_value(self):
        return getattr(self, 'value_%s' % self.attribute.type)

    def _set_value(self, new_value):
        if self.attribute.type == 'option' and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(
                option=new_value)
        setattr(self, 'value_%s' % self.attribute.type, new_value)

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        verbose_name = _('Product Attribute Value')
        verbose_name_plural = _('Product Attribut Values')

    def __unicode__(self):
        return u"%s: %s" % (self.attribute.name, self.value)


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type
    For example, Language
    """
    name = models.CharField(_('Name'), max_length=128)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _('Attribute Option Group')
        verbose_name_plural = _('Attribute Option Groups')


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    group = models.ForeignKey(
        'catalogue.AttributeOptionGroup', related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    def __unicode__(self):
        return self.option

    class Meta:
        abstract = True
        verbose_name = _('Attribute Option')
        verbose_name_plural = _('Attribute Options')


class AbstractAttributeEntity(models.Model):
    """
    Provides an attribute type to enable relationships with other models
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(
        _("Slug"), max_length=255, unique=False, blank=True)
    type = models.ForeignKey(
        'catalogue.AttributeEntityType', related_name='entities',
        verbose_name=_("Type"))

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _('Attribute Entity')
        verbose_name_plural = _('Attribute Entities')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractAttributeEntity, self).save(*args, **kwargs)


class AbstractAttributeEntityType(models.Model):
    """
    Provides the name of the model involved in an entity relationship
    """
    name = models.CharField(_("Name"), max_length=255)
    slug = models.SlugField(
        _("Slug"), max_length=255, unique=False, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _('Attribute Entity Type')
        verbose_name_plural = _('Attribute Entity Types')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(AbstractAttributeEntityType, self).save(*args, **kwargs)


class AbstractOption(models.Model):
    """
    An option that can be selected for a particular item when the product
    is added to the basket.

    For example,  a list ID for an SMS message send, or a personalised message
    to print on a T-shirt.

    This is not the same as an 'attribute' as options do not have a fixed value
    for a particular item.  Instead, option need to be specified by a customer
    when add the item to their basket.
    """
    name = models.CharField(_("Name"), max_length=128)
    code = models.SlugField(_("Code"), max_length=128, unique=True)

    REQUIRED, OPTIONAL = ('Required', 'Optional')
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    type = models.CharField(_("Status"), max_length=128, default=REQUIRED,
                            choices=TYPE_CHOICES)

    class Meta:
        abstract = True
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)
        super(AbstractOption, self).save(*args, **kwargs)

    @property
    def is_required(self):
        return self.type == self.REQUIRED


class MissingProductImage(object):

    def __init__(self, name=None):
        self.name = name if name else settings.OSCAR_MISSING_IMAGE_URL


class AbstractProductImage(models.Model):
    """
    An image of a product
    """
    product = models.ForeignKey(
        'catalogue.Product', related_name='images', verbose_name=_("Product"))
    original = models.ImageField(
        _("Original"), upload_to=settings.OSCAR_IMAGE_FOLDER)
    caption = models.CharField(
        _("Caption"), max_length=200, blank=True, null=True)

    # Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(_("Display Order"), default=0,
        help_text=_("""An image with a display order of
                       zero will be the primary image for a product"""))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        unique_together = ("product", "display_order")
        ordering = ["display_order"]
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')

    def __unicode__(self):
        return u"Image of '%s'" % self.product

    def is_primary(self):
        """
        Return bool if image display order is 0
        """
        return self.display_order == 0

    def resized_image_url(self, width=None, height=None, **kwargs):
        return self.original.url

    @property
    def fullsize_url(self):
        """
        Returns the URL path for this image.  This is intended
        to be overridden in subclasses that want to serve
        images in a specific way.
        """
        return self.resized_image_url()

    @property
    def thumbnail_url(self):
        return self.resized_image_url()
