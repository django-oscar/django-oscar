"""
Vanilla product models
"""
from oscar.product.abstract_models import *

class AttributeType(AbstractAttributeType):
    pass

class ItemType(AbstractItemType):
    pass

class AttributeTypeMembership(AbstractAttributeTypeMembership):
    pass

class Item(AbstractItem):
    pass
    
class Attribute(AbstractAttribute):
    pass
