"""
Vanilla implementation of order models
"""
from django.db import models

from oscar.order.abstract_models import AbstractOrder, AbstractBatch, AbstractBatchItem
from oscar.address.abstract_models import AbstractAddress

class Order(AbstractOrder):
    pass

class Batch(AbstractBatch):
    pass

class DeliveryAddress(AbstractAddress):
    notes = models.TextField(blank=True, null=True) 
    
    class Meta:
        verbose_name_plural = "Delivery addresses"

class BillingAddress(AbstractAddress):
    
    class Meta:
        verbose_name_plural = "Billing addresses"    
    
class BatchItem(AbstractBatchItem):
    pass
    