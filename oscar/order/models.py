"""
Vanilla implementation of order models
"""
from django.db import models

from oscar.order.abstract_models import *
from oscar.address.abstract_models import AbstractShippingAddress, AbstractBillingAddress

class Order(AbstractOrder):
    pass

class OrderNote(AbstractOrderNote):
    pass

class CommunicationEvent(AbstractCommunicationEvent):
    pass

class CommunicationEventType(AbstractCommunicationEventType):
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

class ShippingEvent(AbstractShippingEvent):
    pass

class ShippingEventType(AbstractShippingEventType):
    pass

class PaymentEvent(AbstractPaymentEvent):
    pass

class PaymentEventType(AbstractPaymentEventType):
    pass

class BatchLineAttribute(AbstractBatchLineAttribute):
    pass
    