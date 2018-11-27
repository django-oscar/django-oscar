from django.db import models
from django.db.models import Count
from django.db.models.constants import LOOKUP_SEP

from oscar.core.decorators import deprecated

from .query import FilteredRelationQuery


class AttributeFilter(dict):
    def __init__(self, filter_kwargs):
        super(AttributeFilter, self).__init__()

        num_fields = 0
        for key, value in filter_kwargs.items():
            num_fields += 1
            if LOOKUP_SEP in key:
                field_name, lookup = key.split(LOOKUP_SEP, 1)
                self[field_name] = (lookup, value)
            else:
                self[key] = (None, value)

        self.num_fields = num_fields

    def field_names(self):
        return self.keys()

    def _build_query(self, attribute, annotation_name):
        if (
            attribute.type == attribute.OPTION
            or attribute.type == attribute.MULTI_OPTION
        ):
            return "%s__value_%s__option" % (annotation_name, attribute.type)
        else:
            return "%s__value_%s" % (annotation_name, attribute.type)

    def build_query(self, attribute, annotation_name):
        lookup, value = self[attribute.code]
        query = self._build_query(attribute, annotation_name)
        if lookup is not None:
            return ("%s%s%s" % (query, LOOKUP_SEP, lookup), value)

        return (query, value)


class ProductQuerySet(models.query.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if query is None:  # override query to solve bug in django.
            query = FilteredRelationQuery(model)

        super(ProductQuerySet, self).__init__(model, query, using, hints)

    def filter_by_attributes(self, **filter_kwargs):
        """
        Filter products based on attribute values::

            Product.objects.filter_by_attributes(height=100, google_shopping=True)

        The queries produced look like this::

            SELECT "catalogue_product"."id", "catalogue_product"."structure", "catalogue_product"."upc", "catalogue_product"."parent_id", "catalogue_product"."title", "catalogue_product"."slug", "catalogue_product"."description", "catalogue_product"."product_class_id", "catalogue_product"."rating", "catalogue_product"."date_created", "catalogue_product"."date_updated", "catalogue_product"."is_discountable", "catalogue_product"."vat_rate"  # noqa
                FROM "catalogue_product"
                LEFT OUTER JOIN "catalogue_productattributevalue" HENKIE1
                ON (
                    "catalogue_product"."id" = HENKIE1."product_id" AND (HENKIE1."attribute_id" = 1)
                )
                LEFT OUTER JOIN "catalogue_productattributevalue" HENKIE2
                ON (
                    "catalogue_product"."id" = HENKIE2."product_id" AND (HENKIE2."attribute_id" = 11)
                )
                WHERE (
                    (HENKIE1."value_text" = bah bah AND "catalogue_product"."product_class_id" = 1)
                    OR
                    (HENKIE2."value_text" = bah bah AND "catalogue_product"."product_class_id" = 2)
                )
                ORDER BY "catalogue_product"."date_created"
            DESC

        """
        attribute_filter = AttributeFilter(filter_kwargs)

        # build prefetch query to select relevant attributes of the ProductClass
        ProductAttribute = self.model.attributes.rel.model
        relevant_attributes = ProductAttribute._default_manager.filter(  # pylint: disable=W0212
            code__in=attribute_filter.field_names()
        )
        prefetch_relevant_attributes = models.Prefetch(
            "attributes", queryset=relevant_attributes, to_attr="relevant_attributes"
        )

        # query for the productclasses that support all the filter arguments
        # and prefetch the attributes
        product_classes = self.model.product_class.get_queryset()
        candidate_classes = (
            product_classes.annotate(
                num_fields=models.Count(
                    "attributes",
                    distinct=True,
                    filter=models.Q(
                        attributes__code__in=attribute_filter.field_names()
                    ),
                )
            )
            .filter(num_fields=attribute_filter.num_fields)
            .prefetch_related(prefetch_relevant_attributes)
        )

        result = self.none()

        # build queries per product class, using FilteredRelation for efficiency.
        # combine everything into 1 joined query.
        for product_class in candidate_classes:
            annotations = {}
            filters = {"product_class": product_class}

            for attribute in product_class.relevant_attributes:
                unique_annotation_name = (
                    "%s%i" % (attribute.code, product_class.pk)
                ).upper()
                annotations[unique_annotation_name] = models.FilteredRelation(
                    "attribute_values",
                    condition=models.Q(attribute_values__attribute=attribute),
                )
                query, value = attribute_filter.build_query(
                    attribute, unique_annotation_name
                )
                filters[query] = value

            result |= self.annotate(**annotations).filter(**filters)

        # total number of queries ran for any amount of products, productclasses
        # and attributes queried: 3
        return result

    def base_queryset(self):
        """
        Applies select_related and prefetch_related for commonly related
        models to save on queries
        """
        return self.select_related('product_class')\
            .prefetch_related('children', 'product_options', 'product_class__options', 'stockrecords', 'images') \
            .annotate(num_product_class_options=Count('product_class__options'),
                      num_product_options=Count('product_options'))

    def browsable(self):
        """
        Excludes non-canonical products.
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
