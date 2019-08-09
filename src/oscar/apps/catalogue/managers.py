from collections import defaultdict

from django.db import models
from django.db.models import OuterRef, Exists
from django.db.models.constants import LOOKUP_SEP

from oscar.core.decorators import deprecated
from oscar.core.loading import get_model


class AttributeFilter(dict):
    """
    Utility class used to implement the filter_by_attributes functionality.

    handles lookups, options and multivalue properties, check the tests for
    all features.
    """

    def __init__(self, filter_kwargs):
        super(AttributeFilter, self).__init__()

        for key, value in filter_kwargs.items():
            if LOOKUP_SEP in key:
                field_name, lookup = key.split(LOOKUP_SEP, 1)
                self[field_name] = (lookup, value)
            else:
                self[key] = (None, value)

    def field_names(self):
        return self.keys()

    def _selector(self, attribute_type):
        if attribute_type == "option" or attribute_type == "multi_option":
            return "attribute_values__value_%s__option" % attribute_type
        else:
            return "attribute_values__value_%s" % attribute_type

    def _select_value(self, types, lookup, value):
        _filter = models.Q()
        for _type in types:
            sel = self._selector(_type)
            if lookup is not None:
                sel = "%s%s%s" % (sel, LOOKUP_SEP, lookup)

            kwargs = dict()
            kwargs[sel] = value
            _filter |= models.Q(**kwargs)

        return _filter

    def fast_query(self, attribute_types, queryset):
        qs = queryset
        typedict = defaultdict(list)

        for code, attribute_type in attribute_types:
            typedict[code].append(attribute_type)

        for code, (lookup, value) in self.items():
            selected_values = self._select_value(typedict[code], lookup, value)
            if not selected_values:  # if no value clause can be formed, no result can be formed.
                return queryset.none()

            qs = qs.filter(
                selected_values,
                attribute_values__attribute__code=code,
            )

        return qs


class ProductQuerySet(models.query.QuerySet):

    def filter_by_attributes(self, **filter_kwargs):
        """
        Allows querying by attribute as if the attributes where fields on the
        product::

        >>> first_large_shirt = Product.objects.filter_by_attributes(size="Large").first()
        >>> first_large_shirt.attr.size
        <AttributeOption: Large>
        """
        attribute_filter = AttributeFilter(filter_kwargs)

        ProductAttribute = self.model.attributes.rel.model
        attribute_types = ProductAttribute.objects.values_list("code", "type").filter(
            code__in=attribute_filter.field_names()
        )

        return attribute_filter.fast_query(attribute_types, self)

    def base_queryset(self):
        """
        Applies select_related and prefetch_related for commonly related
        models to save on queries
        """
        Option = get_model('catalogue', 'Option')
        product_class_options = Option.objects.filter(productclass=OuterRef('product_class'))
        product_options = Option.objects.filter(product=OuterRef('pk'))
        return self.select_related('product_class')\
            .prefetch_related('children', 'product_options', 'product_class__options', 'stockrecords', 'images') \
            .annotate(has_product_class_options=Exists(product_class_options),
                      has_product_options=Exists(product_options))

    def browsable(self):
        """
        Excludes non-canonical products and non-public products
        """
        return self.filter(parent=None, is_public=True)

    def browsable_dashboard(self):
        """
        Products that should be browsable in the dashboard.

        Excludes non-canonical products, but includes non-public products.
        """
        return self.filter(parent=None)


@deprecated
class ProductManager(models.Manager):
    """
    Deprecated. Use ProductQuerySet.as_manager() instead.
    """

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def browsable(self):
        return self.get_queryset().browsable()

    def base_queryset(self):
        return self.get_queryset().base_queryset()


class BrowsableProductManager(ProductManager):
    """
    Deprecated. Use Product.objects.browsable() instead.

    The @deprecated decorator isn't applied to the class, because doing
    so would log warnings, and we still initialise this class
    in the Product.browsable for backward compatibility.
    """

    @deprecated
    def get_queryset(self):
        return super().get_queryset().browsable()
