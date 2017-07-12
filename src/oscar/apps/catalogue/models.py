import django

"""
Vanilla product models
"""
from oscar.core.loading import is_model_registered
from oscar.apps.catalogue.abstract_models import *  # noqa

__all__ = []



if not is_model_registered('catalogue', 'Category'):
    class Category(AbstractCategory):
        pass

    __all__.append('Category')


if not is_model_registered('catalogue', 'ProductCategory'):
    class ProductCategory(AbstractProductCategory):
        pass

    __all__.append('ProductCategory')


if not is_model_registered('catalogue', 'Product'):
    class Product(AbstractProduct):
        pass

    __all__.append('Product')


if not is_model_registered('catalogue', 'ProductRecommendation'):
    class ProductRecommendation(AbstractProductRecommendation):
        pass

    __all__.append('ProductRecommendation')


if not is_model_registered('catalogue', 'ProductImage'):
    class ProductImage(AbstractProductImage):
        pass

    __all__.append('ProductImage')


if django.VERSION < (1, 7):
    from . import receivers  # noqa
