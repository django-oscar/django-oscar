from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.order.processing import EventHandler, InvalidShippingEvent
from oscar.apps.order import models
from oscar.test.factories import create_order, create_product
from oscar.apps.basket.models import Basket


class TestEventHandler(TestCase):

    def setUp(self):
        self.order = create_order()
        self.handler = EventHandler()
        self.shipped = models.ShippingEventType.objects.create(name='Shipped')
        self.returned = models.ShippingEventType.objects.create(name='Returned')

    def test_creates_shipping_events_correctly(self):
        self.handler.handle_shipping_event(
            self.order, self.shipped, self.order.lines.all(), [1])

        events = self.order.shipping_events.all()
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual('Shipped', event.event_type.name)

    def test_prevents_event_quantities_higher_than_original_line(self):
        basket = Basket.objects.create()
        basket.add_product(create_product(price=D('10.00')), 5)
        order = create_order(basket=basket)

        # First shipping event
        lines = order.lines.all()
        self.handler.handle_shipping_event(
            order, self.shipped, lines, [4])

        with self.assertRaises(InvalidShippingEvent):
            self.handler.handle_shipping_event(
                order, self.shipped, lines, [4])
