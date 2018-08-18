from django.db import models
from django.db.models import Count

from oscar.core.decorators import deprecated


class ProductQuerySet(models.query.QuerySet):

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
