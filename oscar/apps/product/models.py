"""
Vanilla product models
"""
from oscar.apps.product.abstract_models import *


class ItemClass(AbstractItemClass):
    pass


class Category(AbstractCategory):
    pass


class ItemCategory(AbstractItemCategory):
    pass


class Item(AbstractItem):
    pass
    
    
class AttributeType(AbstractAttributeType):
    pass


class AttributeValueOption(AbstractAttributeValueOption):
    pass


class ItemAttributeValue(AbstractItemAttributeValue):
    pass


class Option(AbstractOption):
    pass


class ProductImage(AbstractProductImage):
    pass

