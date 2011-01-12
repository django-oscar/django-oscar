"""
Clothes shop product models
"""
from oscar.product.abstract_models import *

class ItemClass(AbstractItemClass):
    pass

class Item(AbstractItem):
    label = models.CharField(max_length=32, default='Gucci') 

class AttributeType(AbstractAttributeType):
    pass

class ItemAttributeValue(AbstractItemAttributeValue):
    pass
