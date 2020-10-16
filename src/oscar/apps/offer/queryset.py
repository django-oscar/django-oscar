from django.db import models
from django.db.models import Exists, OuterRef


def product_class_as_queryset(product):
    "Returns a queryset with the product_classes of a product (only one)"
    ProductClass = product._meta.get_field("product_class").related_model
    return ProductClass.objects.filter(
        pk__in=product.__class__.objects.filter(pk=product.pk)
        .annotate(
            _product_class_id=models.Case(
                models.When(
                    structure=product.CHILD, then=models.F("parent__product_class")
                ),
                models.When(
                    structure__in=[product.PARENT, product.STANDALONE],
                    then=models.F("product_class"),
                ),
            )
        )
        .values("_product_class_id")
    )


class RangeQuerySet(models.query.QuerySet):
    """
    This queryset add ``contains_product`` which allows selecting the
    ranges that contain the product in question.
    """
    def contains_product(self, product):
        "Return ranges that contain ``product`` in a single query"
        if product.structure == product.CHILD:
            return self._ranges_that_contain_product(
                product.parent
            ) | self._ranges_that_contain_product(product)
        return self._ranges_that_contain_product(product)

    def _ranges_that_contain_product(self, product):
        Category = product.categories.model
        included_in_subtree = product.categories.filter(
            path__startswith=OuterRef("path")
        )
        category_tree = Category.objects.annotate(
            is_included_in_subtree=Exists(included_in_subtree.values("id"))
        ).filter(is_included_in_subtree=True)

        wide = self.filter(
            ~models.Q(excluded_products=product), includes_all_products=True
        )
        narrow = self.filter(
            ~models.Q(excluded_products=product),
            models.Q(included_products=product)
            | models.Q(included_categories__in=category_tree)
            | models.Q(classes__in=product_class_as_queryset(product)),
            includes_all_products=False,
        )
        return wide | narrow
