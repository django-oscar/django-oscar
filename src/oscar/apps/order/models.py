from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *  # noqa
from oscar.core.loading import is_model_registered

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity']


if not is_model_registered('order', 'Order'):
    class Order(AbstractOrder):
        pass

    __all__.append('Order')


if not is_model_registered('order', 'OrderNote'):
    class OrderNote(AbstractOrderNote):
        pass

    __all__.append('OrderNote')


if not is_model_registered('order', 'OrderStatusChange'):
    class OrderStatusChange(AbstractOrderStatusChange):
        pass

    __all__.append('OrderStatusChange')


if not is_model_registered('order', 'CommunicationEvent'):
    class CommunicationEvent(AbstractCommunicationEvent):
        pass

    __all__.append('CommunicationEvent')


if not is_model_registered('order', 'ShippingAddress'):
    class ShippingAddress(AbstractShippingAddress):
        pass

    __all__.append('ShippingAddress')


if not is_model_registered('order', 'BillingAddress'):
    class BillingAddress(AbstractBillingAddress):
        pass

    __all__.append('BillingAddress')


if not is_model_registered('order', 'Line'):
    class Line(AbstractLine):
        pass

    __all__.append('Line')


if not is_model_registered('order', 'LinePrice'):
    class LinePrice(AbstractLinePrice):
        pass

    __all__.append('LinePrice')


if not is_model_registered('order', 'LineAttribute'):
    class LineAttribute(AbstractLineAttribute):
        pass

    __all__.append('LineAttribute')


if not is_model_registered('order', 'ShippingEvent'):
    class ShippingEvent(AbstractShippingEvent):
        pass

    __all__.append('ShippingEvent')


if not is_model_registered('order', 'ShippingEventType'):
    class ShippingEventType(AbstractShippingEventType):
        pass

    __all__.append('ShippingEventType')


if not is_model_registered('order', 'PaymentEvent'):
    class PaymentEvent(AbstractPaymentEvent):
        pass

    __all__.append('PaymentEvent')


if not is_model_registered('order', 'PaymentEventType'):
    class PaymentEventType(AbstractPaymentEventType):
        pass

    __all__.append('PaymentEventType')


if not is_model_registered('order', 'OrderDiscount'):
    class OrderDiscount(AbstractOrderDiscount):
        pass

    __all__.append('OrderDiscount')

if not is_model_registered('order', 'Surcharge'):
    class Surcharge(AbstractSurcharge):
        pass

    __all__.append('Surcharge')
