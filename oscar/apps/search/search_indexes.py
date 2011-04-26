from haystack import site

from oscar.apps.search.abstract_indexes import AbstractProductIndex
from oscar.core.loading import import_module
product_models = import_module('product.models', ['Item'])


class ProductIndex(AbstractProductIndex):
    pass


site.register(product_models.Item, ProductIndex)

