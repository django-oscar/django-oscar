from django.test import TestCase

from oscar.apps.order.processing import EventHandler
from oscar.apps.order import models
from oscar.test.factories import create_order


class TestEventHandler(TestCase):

    def setUp(self):
        self.order = create_order()
        self.handler = EventHandler()
        self.shipped = models.ShippingEventType.objects.create(name='Shipped')
        self.returned = models.ShippingEventType.objects.create(name='Returned')

    def test_creates_shipping_events_correctly(self):
        self.handler.handle_shipping_event(self.order, self.shipped,
                                           self.order.lines.all(), [1])

        events = self.order.shipping_events.all()
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual('Shipped', event.event_type.name)
