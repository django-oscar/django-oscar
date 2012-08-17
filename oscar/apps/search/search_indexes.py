from haystack import indexes

from django.db.models import get_model


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Base class for products solr index definition.  Overide by creating your
    own copy of oscar.search_indexes.py
    """
    text = indexes.EdgeNgramField(document=True, use_template=True,
                                  template_name='oscar/search/indexes/product/item_text.txt')
    title = indexes.EdgeNgramField(model_attr='title', null=True)
    upc = indexes.CharField(model_attr="upc", null=True)
    date_created = indexes.DateTimeField(model_attr='date_created')
    date_updated = indexes.DateTimeField(model_attr='date_updated')

    def get_model(self):
        return get_model('catalogue', 'Product')

    def index_queryset(self):
        """
        Used when the entire index for model is updated.

        Orders by the most recently updated so that new objects are indexed first
        """
        return self.get_model().objects.order_by('-date_updated')

    def get_updated_field(self):
        """
        Used to specify the field used to determine if an object has been updated

        Can be used to filter the query set when updating the index
        """
        return 'date_updated'


