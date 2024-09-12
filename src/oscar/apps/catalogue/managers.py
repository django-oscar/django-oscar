from collections import defaultdict

from django.db import models
from django.db.models import Exists, OuterRef, Prefetch, F
from django.db.models.constants import LOOKUP_SEP
from treebeard.mp_tree import MP_NodeQuerySet

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
            if (
                not selected_values
            ):  # if no value clause can be formed, no result can be formed.
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
        Option = get_model("catalogue", "Option")
        product_class_options = Option.objects.filter(
            productclass=OuterRef("product_class")
        )
        product_options = Option.objects.filter(product=OuterRef("pk"))
        return (
            self.select_related("product_class")  # pylint:disable=E1102
            .annotate(
                has_product_class_options=Exists(product_class_options),
                has_product_options=Exists(product_options),
            )
            .prefetch_related(
                "children",
                "product_options",
                "product_class__options",
                "stockrecords",
                "images",
            )
        )

    def browsable(self):
        """
        Excludes non-canonical products and non-public products
        """
        return self.filter(parent=None, is_public=True)

    def public(self):
        """
        Excludes non-public products
        """
        return self.filter(is_public=True)

    def browsable_dashboard(self):
        """
        Products that should be browsable in the dashboard.

        Excludes non-canonical products, but includes non-public products.
        """
        return self.filter(parent=None)

    def prefetch_browsable_categories(self, queryset=None):
        """
        Prefetches browsable categories for each product in the queryset,
        including the parent's categories
        """
        if queryset is None:
            Category = get_model("catalogue", "Category")
            queryset = Category.objects.browsable()

        return self.prefetch_related(
            Prefetch(
                "categories",
                queryset=queryset,
                to_attr="_prefetched_browsable_categories",
            ),
            Prefetch(
                "parent__categories",
                queryset=queryset,
                to_attr="_prefetched_browsable_categories",
            ),
        )

    def prefetch_public_children(self, queryset=None):
        """
        Prefetches public children for each product in the queryset
        """
        if queryset is None:
            queryset = self.model.objects.public()

        return self.prefetch_related(
            Prefetch(
                "children",
                queryset=queryset,
                to_attr="_prefetched_public_children",
            )
        )

    def prefetch_attribute_values(self, include_parent_children_attributes=False):
        """
        This prefetches the attribute values for each product in the queryset.
        It also makes sure that for child products, the parent's attribute values are also
        prefetched (excluding the ones the child has).

        Args:
            include_parent_children_attributes (bool): If True, it will also prefetch the attributes for the
            parent's children. You should only set this to true if you're going to iterate over the
            parent's children's attribute values as well, otherwise you're doing useless queries.
        """
        ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
        AttributeOption = get_model("catalogue", "AttributeOption")
        ProductAttribute = get_model("catalogue", "ProductAttribute")

        # The base queryset for both self and parent attribute values.
        prefetch_queryset = (
            ProductAttributeValue.objects.all()
            .select_related("attribute", "value_option", "value_option__group")
            .prefetch_related(
                Prefetch(
                    "value_multi_option",
                    queryset=AttributeOption.objects.select_related("group"),
                )
            )
            .annotate(code=F("attribute__code"))
        )

        # pylint: disable=not-callable
        queryset = self.select_related(
            "product_class", "parent__product_class"
        ).prefetch_related(
            Prefetch(
                "attribute_values",
                queryset=prefetch_queryset,
                to_attr="_prefetched_attribute_values",
            ),
            Prefetch(
                "parent__attribute_values",
                queryset=prefetch_queryset,
                to_attr="_prefetched_parent_attribute_values",
            ),
            # The AttributesQuerysetCache retrieves the attributes for the product class, prefetch those too.
            Prefetch(
                "product_class__attributes",
                queryset=ProductAttribute.objects.all(),
            ),
            Prefetch(
                "parent__product_class__attributes",
                queryset=ProductAttribute.objects.all(),
            ),
        )

        if include_parent_children_attributes:
            queryset = queryset.prefetch_related(
                Prefetch(
                    "children__attribute_values",
                    queryset=prefetch_queryset,
                    to_attr="_prefetched_attribute_values",
                ),
                Prefetch(
                    "children__parent__attribute_values",
                    queryset=prefetch_queryset,
                    to_attr="_prefetched_parent_attribute_values",
                ),
            )

        return queryset


class CategoryQuerySet(MP_NodeQuerySet):
    def browsable(self):
        """
        Excludes non-public categories
        """
        return self.filter(is_public=True, ancestors_are_public=True)
