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

        Method is deprecated. Use BrowsableProductQuerySet instead.
        """
        return self.filter(parent=None)

class BrowsableProductQuerySet(ProductQuerySet):

    def base_queryset(self):
        """
        Excludes non-canonical products
        """
        return super().base_queryset().filter(parent=None)

@deprecated
class ProductManager(models.Manager):
    """
    Uses ProductQuerySet and proxies its methods to allow chaining

    Use of this class is deprecated. Use ProductQuerySet.as_manager() instead.
    """

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def browsable(self):
        return self.get_queryset().browsable()

    def base_queryset(self):
        return self.get_queryset().base_queryset()

@deprecated
class BrowsableProductManager(ProductManager):
    """
    Excludes non-canonical products

    Use of this class is deprecated. Use BrowsableProductQuerySet.as_manager() instead.
    """

    def get_queryset(self):
        return super().get_queryset().browsable()
