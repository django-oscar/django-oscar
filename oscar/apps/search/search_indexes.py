from haystack import site
from oscar.apps.search.abstract_indexes import AbstractProductIndex
from oscar.apps.product.models import Item

class ProductIndex(AbstractProductIndex):
    pass

site.register(Item, ProductIndex)

