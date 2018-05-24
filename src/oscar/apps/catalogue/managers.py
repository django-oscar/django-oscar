from django.db import models
from django.db.models import Count


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


class ProductManager(models.Manager):
    """
    Uses ProductQuerySet and proxies its methods to allow chaining

    Once Django 1.7 lands, this class can probably be removed:
    https://docs.djangoproject.com/en/dev/releases/1.7/#calling-custom-queryset-methods-from-the-manager  # noqa
    """

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def browsable(self):
        return self.get_queryset().browsable()

    def base_queryset(self):
        return self.get_queryset().base_queryset()


class BrowsableProductManager(ProductManager):
    """
    Excludes non-canonical products

    Could be deprecated after Oscar 0.7 is released
    """

    def get_queryset(self):
        return super().get_queryset().browsable()
