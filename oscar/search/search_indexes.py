from haystack.indexes import *
from haystack import site
from oscar.product.models import Item

class ProductIndex(SearchIndex):
    text = EdgeNgramField(document=True, use_template=True)
    title = EdgeNgramField(model_attr='title')
    upc = CharField(model_attr="upc")
    date_created = DateTimeField(model_attr='date_created')
    date_updated = DateTimeField(model_attr='date_updated')

    def get_queryset(self):
        """
        Used when the entire index for model is updated.

        Orders by the most recently updated so that new objects are indexed first
        """
        return Item.objects.order_by('-date_updated')


site.register(Item, ProductIndex)
