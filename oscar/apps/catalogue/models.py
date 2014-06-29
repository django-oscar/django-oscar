"""
Vanilla product models
"""
from django.conf import settings

from oscar.apps.catalogue.abstract_models import *  # noqa


if 'catalogue.ProductClass' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductClass(AbstractProductClass):
        pass


if 'catalogue.Category' not in settings.OSCAR_OVERRIDE_MODELS:
    class Category(AbstractCategory):
        pass


if 'catalogue.ProductCategory' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductCategory(AbstractProductCategory):
        pass


if 'catalogue.Product' not in settings.OSCAR_OVERRIDE_MODELS:
    class Product(AbstractProduct):
        pass


if 'catalogue.ProductRecommendation' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductRecommendation(AbstractProductRecommendation):
        pass


if 'catalogue.ProductAttribute' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductAttribute(AbstractProductAttribute):
        pass


if 'catalogue.ProductAttributeValue' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductAttributeValue(AbstractProductAttributeValue):
        pass


if 'catalogue.AttributeOptionGroup' not in settings.OSCAR_OVERRIDE_MODELS:
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass


if 'catalogue.AttributeOption' not in settings.OSCAR_OVERRIDE_MODELS:
    class AttributeOption(AbstractAttributeOption):
        pass


if 'catalogue.Option' not in settings.OSCAR_OVERRIDE_MODELS:
    class Option(AbstractOption):
        pass


if 'catalogue.ProductImage' not in settings.OSCAR_OVERRIDE_MODELS:
    class ProductImage(AbstractProductImage):
        pass

from .receivers import *  # noqa
