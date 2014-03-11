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


class ProductAttribute(AbstractProductAttribute):
    pass


class ProductAttributeValue(AbstractProductAttributeValue):
    pass


class AttributeOptionGroup(AbstractAttributeOptionGroup):
    pass


class AttributeOption(AbstractAttributeOption):
    pass


class AttributeEntity(AbstractAttributeEntity):
    pass


class AttributeEntityType(AbstractAttributeEntityType):
    pass


class Option(AbstractOption):
    pass


class ProductImage(AbstractProductImage):
    pass


from .receivers import *  # noqa
