from haystack import site
from haystack.exceptions import AlreadyRegistered

from oscar.apps.search.abstract_indexes import AbstractProductIndex
from oscar.core.loading import import_module
product_models = import_module('catalogue.models', ['Product'])


class ProductIndex(AbstractProductIndex):
    pass


try:
    site.register(product_models.Product, ProductIndex)
except AlreadyRegistered:
    # If already registered, it means that a different search app is being
    # used to search products.
    pass

