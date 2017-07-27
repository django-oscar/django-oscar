import os
import logging

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from treebeard.mp_tree import MP_Node

from oscar.core.decorators import deprecated
from oscar.core.utils import slugify
from oscar.core.loading import get_classes, get_class
from oscar.models.fields import NullCharField

ProductManager, BrowsableProductManager = get_classes(
    'catalogue.managers', ['ProductManager', 'BrowsableProductManager'])

Selector = get_class('partner.strategy', 'Selector')


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
    slug = models.SlugField(_('Slug'), max_length=255, db_index=True)

    _slug_separator = '/'
    _full_name_separator = ' > '

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """
        Returns a string representation of the category and it's ancestors,
        e.g. 'Books > Non-fiction > Essential programming'.

        It's rarely used in Oscar's codebase, but used to be stored as a
        CharField and is hence kept for backwards compatibility. It's also
        sufficiently useful to keep around.
        """
        names = [category.name for category in self.get_ancestors_and_self()]
        return self._full_name_separator.join(names)

    @property
    def full_slug(self):
        """
        Returns a string of this category's slug concatenated with the slugs
        of it's ancestors, e.g. 'books/non-fiction/essential-programming'.

        Oscar used to store this as in the 'slug' model field, but this field
        has been re-purposed to only store this category's slug and to not
        include it's ancestors' slugs.
        """
        slugs = [category.slug for category in self.get_ancestors_and_self()]
        return self._slug_separator.join(slugs)

    def generate_slug(self):
        """
        Generates a slug for a category. This makes no attempt at generating
        a unique slug.
        """
        return slugify(self.name)

    def ensure_slug_uniqueness(self):
        """
        Ensures that the category's slug is unique amongst it's siblings.
        This is inefficient and probably not thread-safe.
        """
        unique_slug = self.slug
        siblings = self.get_siblings().exclude(pk=self.pk)
        next_num = 2
        while siblings.filter(slug=unique_slug).exists():
            unique_slug = '{slug}_{end}'.format(slug=self.slug, end=next_num)
            next_num += 1

        if unique_slug != self.slug:
            self.slug = unique_slug
            self.save()

    def save(self, *args, **kwargs):
        """
        Oscar traditionally auto-generated slugs from names. As that is
        often convenient, we still do so if a slug is not supplied through
        other means. If you want to control slug creation, just create
        instances with a slug already set, or expose a field on the
        appropriate forms.
        """
        if self.slug:
            # Slug was supplied. Hands off!
            super(AbstractCategory, self).save(*args, **kwargs)
        else:
            self.slug = self.generate_slug()
            super(AbstractCategory, self).save(*args, **kwargs)
            # We auto-generated a slug, so we need to make sure that it's
            # unique. As we need to be able to inspect the category's siblings
            # for that, we need to wait until the instance is saved. We
            # update the slug and save again if necessary.
            self.ensure_slug_uniqueness()

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
        """
        Our URL scheme means we have to look up the category's ancestors. As
        that is a bit more expensive, we cache the generated URL. That is
        safe even for a stale cache, as the default implementation of
        ProductCategoryView does the lookup via primary key anyway. But if
        you change that logic, you'll have to reconsider the caching
        approach.
        """
        cache_key = 'CATEGORY_URL_%s' % self.pk
        url = cache.get(cache_key)
        if not url:
            url = reverse(
                'catalogue:category',
                kwargs={'category_slug': self.full_slug, 'pk': self.pk})
            cache.set(cache_key, url)
        return url

    class Meta:
        abstract = True
        app_label = 'catalogue'
        ordering = ['path']
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

    recommended_products = models.ManyToManyField(
        'catalogue.Product', through='ProductRecommendation', blank=True,
        verbose_name=_("Recommended products"),
        help_text=_("These are products that are recommended to accompany the "
                    "main product."))

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

    def __str__(self):
        if self.title:
            return self.title
        return self.get_title()

    def get_absolute_url(self):
        """
        Return a product's absolute url
        """
        return reverse('catalogue:detail',
                       kwargs={'product_slug': self.slug, 'pk': self.id})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title())
        super(AbstractProduct, self).save(*args, **kwargs)

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
    def is_shipping_required(self):
        return False

    @property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        return self.num_stockrecords > 0

    @property
    def num_stockrecords(self):
        return len(self.stockrecords.all())

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
