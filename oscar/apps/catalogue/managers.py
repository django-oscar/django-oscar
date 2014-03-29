from django.db import models


class ProductQuerySet(models.query.QuerySet):

    def base_queryset(self):
        """
        Applies select_related and prefetch_related for appropriate related
        Models
        """
        return self.select_related('product_class')\
            .prefetch_related('variants',
                              'product_options',
                              'product_class__options',
                              'stockrecords',
                              'images',
                              )

    def browsable(self):
        """
        Excludes non-canonical Products.
        """
        return self.filter(parent=None)


class ProductManager(models.Manager):
    """
    Uses ProductQuerySet and proxies its methods to allow chaining
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
    """

    def get_queryset(self):
        return super(BrowsableProductManager, self).get_queryset().browsable()
