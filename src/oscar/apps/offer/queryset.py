from django.db import models
from django.db.models.expressions import Subquery

EXPAND_CATEGORY_QUERYSET = """
(SELECT "CATALOGUE_CATEGORY_JOIN"."id" FROM "catalogue_category" AS "CATALOGUE_CATEGORY_BASE"
LEFT JOIN "catalogue_category" AS "CATALOGUE_CATEGORY_JOIN" ON (
    "CATALOGUE_CATEGORY_BASE"."path" LIKE "CATALOGUE_CATEGORY_JOIN"."path" || '%%%%'
)
WHERE "CATALOGUE_CATEGORY_BASE"."id" IN (%(subquery)s))
"""


class ExpandCategoryQueryset(Subquery):
    template = EXPAND_CATEGORY_QUERYSET

    def as_sqlite(self, compiler, connection):
        return super().as_sql(compiler, connection, self.template[1:-1])


class RangeQuerySet(models.query.QuerySet):
    """
    This queryset add ``contains_product`` which allows selecting the
    ranges that contain the product in question.
    """

    def _excluded_products_clause(self, product):
        if product.structure == product.CHILD:
            # child products are excluded from a range if either they are
            # excluded, or their parent.
            return ~(
                models.Q(excluded_products=product)
                | models.Q(excluded_products__id=product.parent_id)
            )
        return ~models.Q(excluded_products=product)

    def _included_products_clause(self, product):
        if product.structure == product.CHILD:
            # child products are included in a range if either they are
            # included, or their parent is included
            return models.Q(included_products=product) | models.Q(
                included_products__id=product.parent_id
            )
        else:
            return models.Q(included_products=product)

    def _productclasses_clause(self, product):
        if product.structure == product.CHILD:
            # child products are included in a range if their parent is
            # included in the range by means of their productclass.
            return models.Q(classes__products__parent_id=product.parent_id)
        return models.Q(classes__id=product.product_class_id)

    def _get_category_ids(self, product):
        if product.structure == product.CHILD:
            # Since a child can not be in a catagory, it must be determined
            # which category the parent is in
            ProductCategory = product.productcategory_set.model
            return ProductCategory.objects.filter(product_id=product.parent_id).values("category_id")

        return product.categories.values("id")

    def contains_product(self, product):
        # the wide query is used to determine which ranges have includes_all_products
        # turned on, we only need to look at explicit exclusions, the other
        # mechanism for adding a product to a range don't need to be checked
        wide = self.filter(
            self._excluded_products_clause(product), includes_all_products=True
        )
        narrow = self.filter(
            self._excluded_products_clause(product),
            self._included_products_clause(product)
            | models.Q(included_categories__in=ExpandCategoryQueryset(self._get_category_ids(product)))
            | self._productclasses_clause(product),
            includes_all_products=False,
        )
        return wide | narrow
