"""
Vanilla implementation of order models
"""
from django.db import models

from oscar.order.abstract_models import *
from oscar.address.abstract_models import AbstractAddress, AbstractShippingAddress, AbstractBillingAddress

class Order(AbstractOrder):
    pass

class Batch(AbstractBatch):
    pass

class ShippingAddress(AbstractShippingAddress):
    pass

class BillingAddress(AbstractBillingAddress):
    pass
    
class BatchLine(AbstractBatchLine):
    pass

class BatchLinePrice(AbstractBatchLinePrice):
    pass

class BatchLineEvent(AbstractBatchLineEvent):
    pass

class BatchLineEventType(AbstractBatchLineEventType):
    pass

class BatchLineAttribute(AbstractBatchLineAttribute):
    pass
    