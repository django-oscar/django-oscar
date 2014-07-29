from oscar.core.loading import is_model_registered
from oscar.apps.order.abstract_models import *  # noqa
from oscar.apps.address.abstract_models import (AbstractShippingAddress,
                                                AbstractBillingAddress)

if not is_model_registered('order', 'Order'):
    class Order(AbstractOrder):
        pass


if not is_model_registered('order', 'OrderNote'):
    class OrderNote(AbstractOrderNote):
        pass


if not is_model_registered('order', 'CommunicationEvent'):
    class CommunicationEvent(AbstractCommunicationEvent):
        pass


if not is_model_registered('order', 'ShippingAddress'):
    class ShippingAddress(AbstractShippingAddress):
        pass


if not is_model_registered('order', 'BillingAddress'):
    class BillingAddress(AbstractBillingAddress):
        pass


if not is_model_registered('order', 'Line'):
    class Line(AbstractLine):
        pass


if not is_model_registered('order', 'LinePrice'):
    class LinePrice(AbstractLinePrice):
        pass


if not is_model_registered('order', 'LineAttribute'):
    class LineAttribute(AbstractLineAttribute):
        pass


if not is_model_registered('order', 'ShippingEvent'):
    class ShippingEvent(AbstractShippingEvent):
        pass


if not is_model_registered('order', 'ShippingEventType'):
    class ShippingEventType(AbstractShippingEventType):
        pass


if not is_model_registered('order', 'PaymentEvent'):
    class PaymentEvent(AbstractPaymentEvent):
        pass


if not is_model_registered('order', 'PaymentEventType'):
    class PaymentEventType(AbstractPaymentEventType):
        pass


if not is_model_registered('order', 'OrderDiscount'):
    class OrderDiscount(AbstractOrderDiscount):
        pass
