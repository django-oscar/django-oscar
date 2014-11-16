import os
from django.utils import six
from datetime import datetime, date
import logging

from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Sum, Count
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.utils.functional import cached_property
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from treebeard.mp_tree import MP_Node

from oscar.core.decorators import deprecated
from oscar.core.utils import slugify
from oscar.core.loading import get_classes, get_model, get_class
from oscar.models.fields import NullCharField, AutoSlugField

ProductManager, BrowsableProductManager = get_classes(
    'catalogue.managers', ['ProductManager', 'BrowsableProductManager'])

Selector = get_class('partner.strategy', 'Selector')


@python_2_unicode_compatible
class AbstractProductClass(models.Model):
    """
    Used for defining options and attributes for a subset of products.
    E.g. Books, DVDs and Toys. A product can only belong to one product class.

    At least one product class must be created when setting up a new
    Oscar deployment.

    Not necessarily equivalent to top-level categories but usually will be.
    """
    name = models.CharField(_('Name'), max_length=128)
    slug = AutoSlugField(_('Slug'), max_length=128, unique=True,
                         populate_from='name')

    #: Some product type don't require shipping (eg digital products) - we use
    #: this field to take some shortcuts in the checkout.
    requires_shipping = models.BooleanField(_("Requires shipping?"),
                                            default=True)

    #: Digital products generally don't require their stock levels to be
    #: tracked.
    track_stock = models.BooleanField(_("Track stock levels?"), default=True)

    #: These are the options (set by the user when they add to basket) for this
    #: item class.  For instance, a product class of "SMS message" would always
    #: require a message to be specified before it could be bought.
    #: Note that you can also set options on a per-product level.
    options = models.ManyToManyField(
        'catalogue.Option', blank=True, verbose_name=_("Options"))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['name']
        verbose_name = _("Product class")
        verbose_name_plural = _("Product classes")

    def __str__(self):
        return self.name

    @property
    def has_attributes(self):
        return self.attributes.exists()


@python_2_unicode_compatible
class AbstractCategory(MP_Node):
    """
    A product category. Merely used for navigational purposes; has no
    effects on business logic.

    Uses django-treebeard.
    """
    name = models.CharField(_('Name'), max_length=255, db_index=True)
    description = models.TextField(_('Description'), blank=True)
    image = models.ImageField(_('Image'), upload_to='categories', blank=True,
                              null=True, max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, db_index=True,
                            editable=False)
    full_name = models.CharField(_('Full Name'), max_length=255,
                                 db_index=True, editable=False)

    _slug_separator = '/'
    _full_name_separator = ' > '

    def __str__(self):
        return self.full_name

    def update_slug(self, commit=True):
        """
        Updates the instance's slug. Use update_children_slugs for updating
        the rest of the tree.
        """
        parent = self.get_parent()
        slug = slugify(self.name)
        # If category has a parent, includes the parents slug in this one
        if parent:
            self.slug = '%s%s%s' % (
                parent.slug, self._slug_separator, slug)
            self.full_name = '%s%s%s' % (
                parent.full_name, self._full_name_separator, self.name)
        else:
            self.slug = slug
            self.full_name = self.name
        if commit:
            self.save()

    def update_children_slugs(self):
        for child in self.get_children():
            child.update_slug()
            child.update_children_slugs()

    def save(self, update_slugs=True, *args, **kwargs):
        if update_slugs:
            self.update_slug(commit=False)

        # If the slug fieldd is updated then validate that it is unique and
        # update the child categories
        update_fields = kwargs.get('update_fields')
        if not update_fields or 'slug' in update_fields:
            # Enforce slug uniqueness here as MySQL can't handle a unique index
            # on the slug field
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
            self.update_children_slugs()
        else:
            super(AbstractCategory, self).save(*args, **kwargs)

    def move(self, target, pos=None):
        """
        Moves the current node and all its descendants to a new position
        relative to another node.

        See https://tabo.pe/projects/django-treebeard/docs/2.0/api.html#treebeard.models.Node.move  # noqa
        """
        super(AbstractCategory, self).move(target, pos)

        # We need to reload self as 'move' doesn't update the current instance,
        # then we iterate over the subtree and call save which automatically
        # updates slugs.
        reloaded_self = self.__class__.objects.get(pk=self.pk)
        reloaded_self.update_slug()
        reloaded_self.update_children_slugs()

    def get_ancestors_and_self(self):
        """
        Gets ancestors and includes itself. Use treebeard's get_ancestors
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        return list(self.get_ancestors()) + [self]

    def get_descendants_and_self(self):
        """
        Gets descendants and includes itself. Use treebeard's get_descendants
        if you don't want to include the category itself. It's a separate
        function as it's commonly used in templates.
        """
        return list(self.get_descendants()) + [self]

    def get_absolute_url(self):
        return reverse('catalogue:category',
                       kwargs={'category_slug': self.slug, 'pk': self.pk})

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['full_name']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def has_children(self):
        return self.get_num_children() > 0

    def get_num_children(self):
        return self.get_children().count()


@python_2_unicode_compatible
class AbstractProductCategory(models.Model):
    """
    Joining model between products and categories. Exists to allow customising.
    """
    product = models.ForeignKey('catalogue.Product', verbose_name=_("Product"))
    category = models.ForeignKey('catalogue.Category',
                                 verbose_name=_("Category"))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['product', 'category']
        unique_together = ('product', 'category')
        verbose_name = _('Product category')
        verbose_name_plural = _('Product categories')

    def __str__(self):
        return u"<productcategory for product '%s'>" % self.product


@python_2_unicode_compatible
class AbstractProduct(models.Model):
    """
    The base product object

    There's three kinds of products; they're distinguished by the structure
    field.

    - A stand alone product. Regular product that lives by itself.
    - A child product. All child products have a parent product. They're a
      specific version of the parent.
    - A parent product. It essentially represents a set of products.

    An example could be a yoga course, which is a parent product. The different
    times/locations of the courses would be associated with the child products.
    """
    STANDALONE, PARENT, CHILD = 'standalone', 'parent', 'child'
    STRUCTURE_CHOICES = (
        (STANDALONE, _('Stand-alone product')),
        (PARENT, _('Parent product')),
        (CHILD, _('Child product'))
    )
    structure = models.CharField(
        _("Product structure"), max_length=10, choices=STRUCTURE_CHOICES,
        default=STANDALONE)

    upc = NullCharField(
        _("UPC"), max_length=64, blank=True, null=True, unique=True,
        help_text=_("Universal Product Code (UPC) is an identifier for "
                    "a product which is not specific to a particular "
                    " supplier. Eg an ISBN for a book."))

    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        verbose_name=_("Parent product"),
        help_text=_("Only choose a parent product if you're creating a child "
                    "product.  For example if this is a size "
                    "4 of a particular t-shirt.  Leave blank if this is a "
                    "stand-alone product (i.e. there is only one version of"
                    " this product)."))

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(pgettext_lazy(u'Product title', u'Title'),
                             max_length=255, blank=True)
    slug = models.SlugField(_('Slug'), max_length=255, unique=False)
    description = models.TextField(_('Description'), blank=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        'catalogue.ProductClass', null=True, on_delete=models.PROTECT,
        verbose_name=_('Product type'), related_name="products",
        help_text=_("Choose what type of product this is"))
    attributes = models.ManyToManyField(
        'catalogue.ProductAttribute',
        through='ProductAttributeValue',
        verbose_name=_("Attributes"),
        help_text=_("A product attribute is something that this product may "
                    "have, such as a size, as specified by its class"))
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        'catalogue.Option', blank=True, verbose_name=_("Product options"),
        help_text=_("Options are values that can be associated with a item "
                    "when it is added to a customer's basket.  This could be "
                    "something like a personalised message to be printed on "
                    "a T-shirt."))

    recommended_products = models.ManyToManyField(
        'catalogue.Product', through='ProductRecommendation', blank=True,
        verbose_name=_("Recommended products"),
        help_text=_("These are products that are recommended to accompany the "
                    "main product."))

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField(_('Rating'), null=True, editable=False)

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(
        _("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        'catalogue.Category', through='ProductCategory',
        verbose_name=_("Categories"))

    #: Determines if a product may be used in an offer. It is illegal to
    #: discount some types of product (e.g. ebooks) and this field helps
    #: merchants from avoiding discounting such products
    #: Note that this flag is ignored for child products; they inherit from
    #: the parent product.
    is_discountable = models.BooleanField(
        _("Is discountable?"), default=True, help_text=_(
            "This flag indicates if this product can be used in an offer "
            "or not"))

    objects = ProductManager()
    browsable = BrowsableProductManager()

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['-date_created']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __init__(self, *args, **kwargs):
        super(AbstractProduct, self).__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    def __str__(self):
        if self.title:
            return self.title
        if self.attribute_summary:
            return u"%s (%s)" % (self.get_title(), self.attribute_summary)
        else:
            return self.get_title()

    def get_absolute_url(self):
        """
        Return a product's absolute url
        """
        return reverse('catalogue:detail',
                       kwargs={'product_slug': self.slug, 'pk': self.id})

    def clean(self):
        """
        Validate a product. Those are the rules:

        +---------------+-------------+--------------+--------------+
        |               | stand alone | parent       | child        |
        +---------------+-------------+--------------+--------------+
        | title         | required    | required     | optional     |
        +---------------+-------------+--------------+--------------+
        | product class | required    | required     | must be None |
        +---------------+-------------+--------------+--------------+
        | parent        | forbidden   | forbidden    | required     |
        +---------------+-------------+--------------+--------------+
        | stockrecords  | 0 or more   | forbidden    | 0 or more    |
        +---------------+-------------+--------------+--------------+
        | categories    | 1 or more   | 1 or more    | forbidden    |
        +---------------+-------------+--------------+--------------+
        | attributes    | optional    | optional     | optional     |
        +---------------+-------------+--------------+--------------+
        | rec. products | optional    | optional     | unsupported  |
        +---------------+-------------+--------------+--------------+
        | options       | optional    | optional     | forbidden    |
        +---------------+-------------+--------------+--------------+

        Because the validation logic is quite complex, validation is delegated
        to the sub method appropriate for the product's structure.
        """
        getattr(self, '_clean_%s' % self.structure)()
        if not self.is_parent:
            self.attr.validate_attributes()

    def _clean_standalone(self):
        """
        Validates a stand-alone product
        """
        if not self.title:
            raise ValidationError(_("Your product must have a title."))
        if not self.product_class:
            raise ValidationError(_("Your product must have a product class."))
        if self.parent_id:
            raise ValidationError(_("Only child products can have a parent."))

    def _clean_child(self):
        """
        Validates a child product
        """
        if not self.parent_id:
            raise ValidationError(_("A child product needs a parent."))
        if self.parent_id and not self.parent.is_parent:
            raise ValidationError(
                _("You can only assign child products to parent products."))
        if self.product_class:
            raise ValidationError(
                _("A child product can't have a product class."))
        if self.pk and self.categories.exists():
            raise ValidationError(
                _("A child product can't have a category assigned."))
        # Note that we only forbid options on product level
        if self.pk and self.product_options.exists():
            raise ValidationError(
                _("A child product can't have options."))

    def _clean_parent(self):
        """
        Validates a parent product.
        """
        self._clean_standalone()
        if self.has_stockrecords:
            raise ValidationError(
                _("A parent product can't have stockrecords."))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title())
        super(AbstractProduct, self).save(*args, **kwargs)
        self.attr.save()

    # Properties

    @property
    def is_standalone(self):
        return self.structure == self.STANDALONE

    @property
    def is_parent(self):
        return self.structure == self.PARENT

    @property
    def is_child(self):
        return self.structure == self.CHILD

    def can_be_parent(self, give_reason=False):
        """
        Helps decide if a the product can be turned into a parent product.
        """
        reason = None
        if self.is_child:
            reason = _('The specified parent product is a child product.')
        if self.has_stockrecords:
            reason = _(
                "One can't add a child product to a product with stock"
                " records.")
        is_valid = reason is None
        if give_reason:
            return is_valid, reason
        else:
            return is_valid

    @property
    def options(self):
        """
        Returns a set of all valid options for this product.
        It's possible to have options product class-wide, and per product.
        """
        pclass_options = self.get_product_class().options.all()
        return set(pclass_options) or set(self.product_options.all())

    @property
    def is_shipping_required(self):
        return self.get_product_class().requires_shipping

    @property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        return self.stockrecords.exists()

    @property
    def num_stockrecords(self):
        return self.stockrecords.count()

    @property
    def attribute_summary(self):
        """
        Return a string of all of a product's attributes
        """
        attributes = self.attribute_values.all()
        pairs = [attribute.summary() for attribute in attributes]
        return ", ".join(pairs)

    # The two properties below are deprecated because determining minimum
    # price is not as trivial as it sounds considering multiple stockrecords,
    # currencies, tax, etc.
    # The current implementation is very naive and only works for a limited
    # set of use cases.
    # At the very least, we should pass in the request and
    # user. Hence, it's best done as an extension to a Strategy class.
    # Once that is accomplished, these properties should be removed.

    @property
    @deprecated
    def min_child_price_incl_tax(self):
        """
        Return minimum child product price including tax.
        """
        return self._min_child_price('incl_tax')

    @property
    @deprecated
    def min_child_price_excl_tax(self):
        """
        Return minimum child product price excluding tax.

        This is a very naive approach; see the deprecation notice above. And
        only use it for display purposes (e.g. "new Oscar shirt, prices
        starting from $9.50").
        """
        return self._min_child_price('excl_tax')

    def _min_child_price(self, prop):
        """
        Return minimum child product price.

        This is for visual purposes only. It ignores currencies, most of the
        Strategy logic for selecting stockrecords, knows nothing about the
        current user or request, etc. It's only here to ensure
        backwards-compatibility; the previous implementation wasn't any
        better.
        """
        strategy = Selector().strategy()

        children_stock = strategy.select_children_stockrecords(self)
        prices = [
            strategy.pricing_policy(child, stockrecord)
            for child, stockrecord in children_stock]
        raw_prices = sorted([getattr(price, prop) for price in prices])
        return raw_prices[0] if raw_prices else None

    # The properties below are based on deprecated naming conventions

    @property
    @deprecated
    def variants(self):
        """
        Provide backwards-compatible way to access a parent products children
        """
        return self.children

    @property
    @deprecated
    def is_top_level(self):
        """
        Test if this product is a stand-alone or parent product
        """
        return self.is_standalone or self.is_parent

    @property
    @deprecated
    def is_group(self):
        """
        Test if this is a parent product
        """
        return self.is_parent

    @property
    @deprecated
    def is_variant(self):
        """Return True if a product is not a top level product"""
        return self.is_child

    @property
    @deprecated
    def min_variant_price_incl_tax(self):
        """
        Return minimum variant price including tax
        """
        return self._min_child_price('price_incl_tax')

    @property
    @deprecated
    def min_variant_price_excl_tax(self):
        """
        Return minimum variant price excluding tax
        """
        return self._min_child_price('price_excl_tax')

    # Wrappers for child products

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title
    get_title.short_description = pgettext_lazy(u"Product title", u"Title")

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class
    get_product_class.short_description = _("Product class")

    def get_is_discountable(self):
        """
        At the moment, is_discountable can't be set individually for child
        products; they inherit it from their parent.
        """
        if self.is_child:
            return self.parent.is_discountable
        else:
            return self.is_discountable

    def get_categories(self):
        """
        Return a product's categories or parent's if there is a parent product.
        """
        if self.is_child:
            return self.parent.categories
        else:
            return self.categories
    get_categories.short_description = _("Categories")

    # Images

    def get_missing_image(self):
        """
        Returns a missing image object.
        """
        # This class should have a 'name' property so it mimics the Django file
        # field.
        return MissingProductImage()

    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        images = self.images.all()
        ordering = self.images.model.Meta.ordering
        if not ordering or ordering[0] != 'display_order':
            # Only apply order_by() if a custom model doesn't use default
            # ordering. Applying order_by() busts the prefetch cache of
            # the ProductManager
            images = images.order_by('display_order')
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the ProductImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            return {
                'original': self.get_missing_image(),
                'caption': '',
                'is_missing': True}

    # Updating methods

    def update_rating(self):
        """
        Recalculate rating field
        """
        self.rating = self.calculate_rating()
        self.save()
    update_rating.alters_data = True

    def calculate_rating(self):
        """
        Calculate rating value
        """
        result = self.reviews.filter(
            status=self.reviews.model.APPROVED
        ).aggregate(
            sum=Sum('score'), count=Count('id'))
        reviews_sum = result['sum'] or 0
        reviews_count = result['count'] or 0
        rating = None
        if reviews_count > 0:
            rating = float(reviews_sum) / reviews_count
        return rating

    def has_review_by(self, user):
        if user.is_anonymous():
            return False
        return self.reviews.filter(user=user).exists()

    def is_review_permitted(self, user):
        """
        Determines whether a user may add a review on this product.

        Default implementation respects OSCAR_ALLOW_ANON_REVIEWS and only
        allows leaving one review per user and product.

        Override this if you want to alter the default behaviour; e.g. enforce
        that a user purchased the product to be allowed to leave a review.
        """
        if user.is_authenticated() or settings.OSCAR_ALLOW_ANON_REVIEWS:
            return not self.has_review_by(user)
        else:
            return False

    @cached_property
    def num_approved_reviews(self):
        return self.reviews.filter(
            status=self.reviews.model.APPROVED).count()


class AbstractProductRecommendation(models.Model):
    """
    'Through' model for product recommendations
    """
    primary = models.ForeignKey(
        'catalogue.Product', related_name='primary_recommendations',
        verbose_name=_("Primary product"))
    recommendation = models.ForeignKey(
        'catalogue.Product', verbose_name=_("Recommended product"))
    ranking = models.PositiveSmallIntegerField(
        _('Ranking'), default=0,
        help_text=_('Determines order of the products. A product with a higher'
                    ' value will appear before one with a lower ranking.'))

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['primary', '-ranking']
        unique_together = ('primary', 'recommendation')
        verbose_name = _('Product recommendation')
        verbose_name_plural = _('Product recomendations')


class ProductAttributesContainer(object):
    """
    Stolen liberally from django-eav, but simplified to be product-specific

    To set attributes on a product, use the `attr` attribute:

        product.attr.weight = 125
    """

    def __setstate__(self, state):
        self.__dict__ = state
        self.initialised = False

    def __init__(self, product):
        self.product = product
        self.initialised = False

    def __getattr__(self, name):
        if not name.startswith('_') and not self.initialised:
            values = self.get_values().select_related('attribute')
            for v in values:
                setattr(self, v.attribute.code, v.value)
            self.initialised = True
            return getattr(self, name)
        raise AttributeError(
            _("%(obj)s has no attribute named '%(attr)s'") % {
                'obj': self.product.get_product_class(), 'attr': name})

    def validate_attributes(self):
        for attribute in self.get_all_attributes():
            value = getattr(self, attribute.code, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(
                        _("%(attr)s attribute cannot be blank") %
                        {'attr': attribute.code})
            else:
                try:
                    attribute.validate_value(value)
                except ValidationError as e:
                    raise ValidationError(
                        _("%(attr)s attribute %(err)s") %
                        {'attr': attribute.code, 'err': e})

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


@python_2_unicode_compatible
class AbstractProductAttribute(models.Model):
    """
    Defines an attribute for a product class. (For example, number_of_pages for
    a 'book' class)
    """
    product_class = models.ForeignKey(
        'catalogue.ProductClass', related_name='attributes', blank=True,
        null=True, verbose_name=_("Product type"))
    name = models.CharField(_('Name'), max_length=128)
    code = models.SlugField(
        _('Code'), max_length=128,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z\-_][0-9a-zA-Z\-_]*$',
            message=_("Code can only contain the letters a-z, A-Z, digits, "
                      "minus and underscores, and can't start with a digit"))])

    # Attribute types
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    RICHTEXT = "richtext"
    DATE = "date"
    OPTION = "option"
    ENTITY = "entity"
    FILE = "file"
    IMAGE = "image"
    TYPE_CHOICES = (
        (TEXT, _("Text")),
        (INTEGER, _("Integer")),
        (BOOLEAN, _("True / False")),
        (FLOAT, _("Float")),
        (RICHTEXT, _("Rich Text")),
        (DATE, _("Date")),
        (OPTION, _("Option")),
        (ENTITY, _("Entity")),
        (FILE, _("File")),
        (IMAGE, _("Image")),
    )
    type = models.CharField(
        choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))

    option_group = models.ForeignKey(
        'catalogue.AttributeOptionGroup', blank=True, null=True,
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option"'))
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['code']
        verbose_name = _('Product attribute')
        verbose_name_plural = _('Product attributes')

    @property
    def is_option(self):
        return self.type == self.OPTION

    @property
    def is_file(self):
        return self.type in [self.FILE, self.IMAGE]

    def __str__(self):
        return self.name

    def save_value(self, product, value):
        ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
        try:
            value_obj = product.attribute_values.get(attribute=self)
        except ProductAttributeValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = ProductAttributeValue.objects.create(
                product=product, attribute=self)

        if self.is_file:
            # File fields in Django are treated differently, see
            # django.db.models.fields.FileField and method save_form_data
            if value is None:
                # No change
                return
            elif value is False:
                # Delete file
                value_obj.delete()
            else:
                # New uploaded file
                value_obj.value = value
                value_obj.save()
        else:
            if value is None or value == '':
                value_obj.delete()
                return
            if value != value_obj.value:
                value_obj.value = value
                value_obj.save()

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.type)
        validator(value)

    # Validators

    def _validate_text(self, value):
        if not isinstance(value, six.string_types):
            raise ValidationError(_("Must be str or unicode"))
    _validate_richtext = _validate_text

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_entity(self, value):
        if not isinstance(value, models.Model):
            raise ValidationError(_("Must be a model instance"))

    def _validate_option(self, value):
        if not isinstance(value, get_model('catalogue', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))
        valid_values = self.option_group.options.values_list(
            'option', flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                _("%(enum)s is not a valid choice for %(attr)s") %
                {'enum': value, 'attr': self})

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file field"))
    _validate_image = _validate_file


@python_2_unicode_compatible
class AbstractProductAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between catalogue.Product and
    catalogue.ProductAttribute.  This specifies the value of the attribute for
    a particular product

    For example: number_of_pages = 295
    """
    attribute = models.ForeignKey(
        'catalogue.ProductAttribute', verbose_name=_("Attribute"))
    product = models.ForeignKey(
        'catalogue.Product', related_name='attribute_values',
        verbose_name=_("Product"))

    value_text = models.TextField(_('Text'), blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
    value_option = models.ForeignKey(
        'catalogue.AttributeOption', blank=True, null=True,
        verbose_name=_("Value option"))
    value_file = models.FileField(
        upload_to=settings.OSCAR_IMAGE_FOLDER, max_length=255,
        blank=True, null=True)
    value_image = models.ImageField(
        upload_to=settings.OSCAR_IMAGE_FOLDER, max_length=255,
        blank=True, null=True)
    value_entity = GenericForeignKey(
        'entity_content_type', 'entity_object_id')

    entity_content_type = models.ForeignKey(
        ContentType, null=True, blank=True, editable=False)
    entity_object_id = models.PositiveIntegerField(
        null=True, blank=True, editable=False)

    def _get_value(self):
        return getattr(self, 'value_%s' % self.attribute.type)

    def _set_value(self, new_value):
        if self.attribute.is_option and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(
                option=new_value)
        setattr(self, 'value_%s' % self.attribute.type, new_value)

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        unique_together = ('attribute', 'product')
        verbose_name = _('Product attribute value')
        verbose_name_plural = _('Product attribute values')

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in product summaries.
        """
        return u"%s: %s" % (self.attribute.name, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.attribute.type
        return getattr(self, property_name, self.value)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def _entity_as_text(self):
        """
        Returns the unicode representation of the related model. You likely
        want to customise this (and maybe _entity_as_html) if you use entities.
        """
        return six.text_type(self.value)

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_html property and
        return e.g. an <img> tag.  Defaults to the _as_text representation.
        """
        property_name = '_%s_as_html' % self.attribute.type
        return getattr(self, property_name, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)


@python_2_unicode_compatible
class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """
    name = models.CharField(_('Name'), max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'catalogue'
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


@python_2_unicode_compatible
class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    group = models.ForeignKey(
        'catalogue.AttributeOptionGroup', related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    def __str__(self):
        return self.option

    class Meta:
        abstract = True
        app_label = 'catalogue'
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')


@python_2_unicode_compatible
class AbstractOption(models.Model):
    """
    An option that can be selected for a particular item when the product
    is added to the basket.

    For example,  a list ID for an SMS message send, or a personalised message
    to print on a T-shirt.

    This is not the same as an 'attribute' as options do not have a fixed value
    for a particular item.  Instead, option need to be specified by a customer
    when they add the item to their basket.
    """
    name = models.CharField(_("Name"), max_length=128)
    code = AutoSlugField(_("Code"), max_length=128, unique=True,
                         populate_from='name')

    REQUIRED, OPTIONAL = ('Required', 'Optional')
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    type = models.CharField(_("Status"), max_length=128, default=REQUIRED,
                            choices=TYPE_CHOICES)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.name

    @property
    def is_required(self):
        return self.type == self.REQUIRED


class MissingProductImage(object):

    """
    Mimics a Django file field by having a name property.

    sorl-thumbnail requires all it's images to be in MEDIA_ROOT. This class
    tries symlinking the default "missing image" image in STATIC_ROOT
    into MEDIA_ROOT for convenience, as that is necessary every time an Oscar
    project is setup. This avoids the less helpful NotFound IOError that would
    be raised when sorl-thumbnail tries to access it.
    """

    def __init__(self, name=None):
        self.name = name if name else settings.OSCAR_MISSING_IMAGE_URL
        media_file_path = os.path.join(settings.MEDIA_ROOT, self.name)
        # don't try to symlink if MEDIA_ROOT is not set (e.g. running tests)
        if settings.MEDIA_ROOT and not os.path.exists(media_file_path):
            self.symlink_missing_image(media_file_path)

    def symlink_missing_image(self, media_file_path):
        static_file_path = find('oscar/img/%s' % self.name)
        if static_file_path is not None:
            try:
                os.symlink(static_file_path, media_file_path)
            except OSError:
                raise ImproperlyConfigured((
                    "Please copy/symlink the "
                    "'missing image' image at %s into your MEDIA_ROOT at %s. "
                    "This exception was raised because Oscar was unable to "
                    "symlink it for you.") % (media_file_path,
                                              settings.MEDIA_ROOT))
            else:
                logging.info((
                    "Symlinked the 'missing image' image at %s into your "
                    "MEDIA_ROOT at %s") % (media_file_path,
                                           settings.MEDIA_ROOT))


@python_2_unicode_compatible
class AbstractProductImage(models.Model):
    """
    An image of a product
    """
    product = models.ForeignKey(
        'catalogue.Product', related_name='images', verbose_name=_("Product"))
    original = models.ImageField(
        _("Original"), upload_to=settings.OSCAR_IMAGE_FOLDER, max_length=255)
    caption = models.CharField(_("Caption"), max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        _("Display order"), default=0,
        help_text=_("An image with a display order of zero will be the primary"
                    " image for a product"))
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'catalogue'
        # Any custom models should ensure that this ordering is unchanged, or
        # your query count will explode. See AbstractProduct.primary_image.
        ordering = ["display_order"]
        unique_together = ("product", "display_order")
        verbose_name = _('Product image')
        verbose_name_plural = _('Product images')

    def __str__(self):
        return u"Image of '%s'" % self.product

    def is_primary(self):
        """
        Return bool if image display order is 0
        """
        return self.display_order == 0

    def delete(self, *args, **kwargs):
        """
        Always keep the display_order as consecutive integers. This avoids
        issue #855.
        """
        super(AbstractProductImage, self).delete(*args, **kwargs)
        for idx, image in enumerate(self.product.images.all()):
            image.display_order = idx
            image.save()
