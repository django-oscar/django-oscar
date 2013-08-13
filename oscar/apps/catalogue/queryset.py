from django.db.models.query import QuerySet
from django.db.models.query_utils import Q


class ProductBrowsableQuerySet(QuerySet):
    def __init__(self, *args, **kwargs):
        super(ProductBrowsableQuerySet, self).__init__(*args, **kwargs)
        # this will be a default starting query
        self.query.add_q(Q(parent=None))

    def base_queryset(self):
        """
        Return ``QuerySet`` for with related content pre-loaded.
        The ``QuerySet`` returns unfiltered results for further filtering.
        """
        return self.select_related(
            'product_class',
        ).prefetch_related(
            'variants',
            'product_options',
            'product_class__options',
            'stockrecord',
            'images',
        ).all()
