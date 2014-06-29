from django.conf import settings

from oscar.apps.order.abstract_models import *  # noqa
from oscar.apps.address.abstract_models import (AbstractShippingAddress,
                                                AbstractBillingAddress)


if 'order.Order' not in settings.OSCAR_OVERRIDE_MODELS:
    class Order(AbstractOrder):
        pass


if 'order.OrderNote' not in settings.OSCAR_OVERRIDE_MODELS:
    class OrderNote(AbstractOrderNote):
        pass


if 'order.CommunicationEvent' not in settings.OSCAR_OVERRIDE_MODELS:
    class CommunicationEvent(AbstractCommunicationEvent):
        pass


if 'order.ShippingAddress' not in settings.OSCAR_OVERRIDE_MODELS:
    class ShippingAddress(AbstractShippingAddress):
        pass


if 'order.BillingAddress' not in settings.OSCAR_OVERRIDE_MODELS:
    class BillingAddress(AbstractBillingAddress):
        pass


if 'order.Line' not in settings.OSCAR_OVERRIDE_MODELS:
    class Line(AbstractLine):
        pass


if 'order.LinePrice' not in settings.OSCAR_OVERRIDE_MODELS:
    class LinePrice(AbstractLinePrice):
        pass


if 'order.LineAttribute' not in settings.OSCAR_OVERRIDE_MODELS:
    class LineAttribute(AbstractLineAttribute):
        pass


if 'order.ShippingEvent' not in settings.OSCAR_OVERRIDE_MODELS:
    class ShippingEvent(AbstractShippingEvent):
        pass


if 'order.ShippingEventType' not in settings.OSCAR_OVERRIDE_MODELS:
    class ShippingEventType(AbstractShippingEventType):
        pass


if 'order.PaymentEvent' not in settings.OSCAR_OVERRIDE_MODELS:
    class PaymentEvent(AbstractPaymentEvent):
        pass


if 'order.PaymentEventType' not in settings.OSCAR_OVERRIDE_MODELS:
    class PaymentEventType(AbstractPaymentEventType):
        pass


if 'order.OrderDiscount' not in settings.OSCAR_OVERRIDE_MODELS:
    class OrderDiscount(AbstractOrderDiscount):
        pass
