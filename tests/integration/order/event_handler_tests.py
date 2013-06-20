from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.order.processing import EventHandler
from oscar.apps.order import models, exceptions
from oscar.test.factories import create_order, create_product
from oscar.apps.basket.models import Basket


class TestEventHandler(TestCase):

    def setUp(self):
        self.order = create_order()
        self.handler = EventHandler()
        self.shipped = models.ShippingEventType.objects.create(
            name='Shipped')
        self.returned = models.ShippingEventType.objects.create(
            name='Returned')

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

        with self.assertRaises(exceptions.InvalidShippingEvent):
            self.handler.handle_shipping_event(
                order, self.shipped, lines, [4])


class TestTotalCalculation(TestCase):

    def setUp(self):
        self.order = create_order()
        self.handler = EventHandler()
        basket = Basket.objects.create()
        basket.add_product(create_product(price=D('10.00')), 5)
        self.order = create_order(basket=basket)
        self.settled = models.PaymentEventType.objects.create(
            name='Settled')

    def test_normal_payment_sequence(self):
        # First payment event
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEquals(2 * D('10.00'), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities)

        # Second payment
        line_quantities = [3]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEquals(3 * D('10.00'), total)

    def test_invalid_payment_sequence(self):
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEquals(2 * D('10.00'), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities)

        with self.assertRaises(exceptions.InvalidPaymentEvent):
            self.handler.calculate_payment_event_subtotal(
                self.settled, self.order.lines.all(), [4])
