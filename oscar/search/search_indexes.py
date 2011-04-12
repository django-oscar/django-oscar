from haystack import site
from oscar.search.abstract_indexes import AbstractProductIndex
from oscar.product.models import Item

class ProductIndex(AbstractProductIndex):
    pass

site.register(Item, ProductIndex)

