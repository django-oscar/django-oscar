import django

"""
Vanilla product models
"""
from oscar.core.loading import is_model_registered
from oscar.apps.catalogue.abstract_models import *  # noqa


if not is_model_registered('catalogue', 'ProductClass'):
    class ProductClass(AbstractProductClass):
        pass


if not is_model_registered('catalogue', 'Category'):
    class Category(AbstractCategory):
        pass


if not is_model_registered('catalogue', 'ProductCategory'):
    class ProductCategory(AbstractProductCategory):
        pass


if not is_model_registered('catalogue', 'Product'):
    class Product(AbstractProduct):
        pass


if not is_model_registered('catalogue', 'ProductRecommendation'):
    class ProductRecommendation(AbstractProductRecommendation):
        pass


if not is_model_registered('catalogue', 'ProductAttribute'):
    class ProductAttribute(AbstractProductAttribute):
        pass


if not is_model_registered('catalogue', 'ProductAttributeValue'):
    class ProductAttributeValue(AbstractProductAttributeValue):
        pass


if not is_model_registered('catalogue', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass


if not is_model_registered('catalogue', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        pass


if not is_model_registered('catalogue', 'Option'):
    class Option(AbstractOption):
        pass


if not is_model_registered('catalogue', 'ProductImage'):
    class ProductImage(AbstractProductImage):
        pass


if django.VERSION < (1, 7):
    from . import receivers  # noqa
