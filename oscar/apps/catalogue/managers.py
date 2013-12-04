from django.db import models


class ProductManager(models.Manager):

    def base_queryset(self):
        """
        Return ``QuerySet`` with related content pre-loaded.
        """
        return self.get_query_set().select_related(
            'product_class',
            ).prefetch_related(
            'variants',
            'product_options',
            'product_class__options',
            'stockrecords',
            'images',
            ).all()


class BrowsableProductManager(ProductManager):
    """
    Excludes non-canonical products
    """

    def get_query_set(self):
        return super(BrowsableProductManager, self).get_query_set().filter(
            parent=None)
