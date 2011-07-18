from haystack.indexes import *

from oscar.core.loading import import_module
product_models = import_module('catalogue.models', ['Product'])


class AbstractProductIndex(SearchIndex):
    u"""
    Base class for products solr index definition.  Overide by creating your
    own copy of oscar.search_indexes.py
    """
    text = EdgeNgramField(document=True, use_template=True, template_name='search/indexes/product/item_text.txt')
    title = EdgeNgramField(model_attr='title', null=True)
    upc = CharField(model_attr="upc", null=True)
    product_score = FloatField(model_attr="score")
    date_created = DateTimeField(model_attr='date_created')
    date_updated = DateTimeField(model_attr='date_updated')

    def index_queryset(self):
        """
        Used when the entire index for model is updated.

        Orders by the most recently updated so that new objects are indexed first
        """
        return product_models.Product.objects.order_by('-date_updated')

    def get_updated_field(self):
        u"""
        Used to specify the field used to determine if an object has been updated

        Can be used to filter the query set when updating the index
        """
        return 'date_updated'


