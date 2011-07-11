"""
Vanilla product models
"""
from oscar.apps.catalogue.abstract_models import *


class ProductClass(AbstractProductClass):
    pass


class Category(AbstractCategory):
    pass


class ProductCategory(AbstractProductCategory):
    pass


class Product(AbstractProduct):
    pass
    
    
class AttributeType(AbstractAttributeType):
    pass


class AttributeValueOption(AbstractAttributeValueOption):
    pass


class ProductAttributeValue(AbstractProductAttributeValue):
    pass


class Option(AbstractOption):
    pass


class ProductImage(AbstractProductImage):
    pass

