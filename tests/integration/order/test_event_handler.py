from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.order.processing import EventHandler
from oscar.apps.order import models, exceptions
from oscar.test import factories
from oscar.test.basket import add_product


class TestEventHandler(TestCase):

    def setUp(self):
        self.order = factories.create_order()
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

    def test_verifies_lines_has_passed_shipping_event(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D('10.00'), 5)
        order = factories.create_order(basket=basket)

        lines = order.lines.all()
        self.handler.handle_shipping_event(
            order, self.shipped, lines, [4])

        self.assertTrue(self.handler.have_lines_passed_shipping_event(
            order, lines, [3], self.shipped))
        self.assertTrue(self.handler.have_lines_passed_shipping_event(
            order, lines, [4], self.shipped))
        self.assertFalse(self.handler.have_lines_passed_shipping_event(
            order, lines, [5], self.shipped))

    def test_prevents_event_quantities_higher_than_original_line(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D('10.00'), 5)
        order = factories.create_order(basket=basket)

        # First shipping event
        lines = order.lines.all()
        self.handler.handle_shipping_event(
            order, self.shipped, lines, [4])

        with self.assertRaises(exceptions.InvalidShippingEvent):
            self.handler.handle_shipping_event(
                order, self.shipped, lines, [4])


class TestTotalCalculation(TestCase):

    def setUp(self):
        self.order = factories.create_order()
        self.handler = EventHandler()
        basket = factories.create_basket(empty=True)
        add_product(basket, D('10.00'), 5)
        self.order = factories.create_order(basket=basket)
        self.settled = models.PaymentEventType.objects.create(
            name='Settled')

    def test_normal_payment_sequence(self):
        # First payment event
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEqual(2 * D('10.00'), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities)

        # Second payment
        line_quantities = [3]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEqual(3 * D('10.00'), total)

    def test_invalid_payment_sequence(self):
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities)
        self.assertEqual(2 * D('10.00'), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities)

        with self.assertRaises(exceptions.InvalidPaymentEvent):
            self.handler.calculate_payment_event_subtotal(
                self.settled, self.order.lines.all(), [4])
