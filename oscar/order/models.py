"""
Vanilla implementation of order models
"""
from django.db import models

from oscar.order.abstract_models import *
from oscar.address.abstract_models import AbstractAddress, AbstractDeliveryAddress, AbstractBillingAddress

class Order(AbstractOrder):
    pass

class Batch(AbstractBatch):
    pass

class DeliveryAddress(AbstractDeliveryAddress):
    pass

class BillingAddress(AbstractBillingAddress):
    pass
    
class BatchItem(AbstractBatchItem):
    pass

class BatchItemAttribute(AbstractBatchItemAttribute):
    pass
    