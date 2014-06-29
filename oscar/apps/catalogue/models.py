import django

"""
Vanilla product models
"""
from oscar.apps.catalogue.abstract_models import *  # noqa


class ProductClass(AbstractProductClass):
    pass


class Category(AbstractCategory):
    pass


class ProductCategory(AbstractProductCategory):
    pass


class Product(AbstractProduct):
    pass


class ProductRecommendation(AbstractProductRecommendation):
    pass


class ProductAttribute(AbstractProductAttribute):
    pass


class ProductAttributeValue(AbstractProductAttributeValue):
    pass


class AttributeOptionGroup(AbstractAttributeOptionGroup):
    pass


class AttributeOption(AbstractAttributeOption):
    pass


class Option(AbstractOption):
    pass


class ProductImage(AbstractProductImage):
    pass


if django.VERSION < (1, 7):
    from . import receivers
