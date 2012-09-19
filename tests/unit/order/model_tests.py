from datetime import timedelta
from decimal import Decimal as D

from django.test import TestCase
from django.utils import timezone
import mock

from oscar.apps.address.models import Country
from oscar.apps.basket.models import Basket
from oscar.apps.order.models import ShippingAddress, Order, Line, \
        ShippingEvent, ShippingEventType, ShippingEventQuantity, OrderNote, \
        OrderDiscount
from oscar.apps.order.exceptions import (InvalidOrderStatus, InvalidLineStatus,
                                         InvalidShippingEvent)
from oscar.test.helpers import create_order, create_product, create_offer

ORDER_PLACED = 'order_placed'


class ShippingAddressTest(TestCase):
    fixtures = ['countries.json']

    def test_titleless_salutation_is_stripped(self):
        country = Country.objects.get(iso_3166_1_a2='GB')
        a = ShippingAddress.objects.create(last_name='Barrington', line1="75 Smith Road", postcode="N4 8TY", country=country)
        self.assertEquals("Barrington", a.salutation())


class OrderStatusPipelineTests(TestCase):

    def setUp(self):
        Order.pipeline = {'PENDING': ('SHIPPED', 'CANCELLED'),
                          'SHIPPED': ('COMPLETE',)}
        Order.cascade = {'SHIPPED': 'SHIPPED'}

    def tearDown(self):
        Order.pipeline = {}
        Order.cascade = {}

    def test_available_statuses_for_pending(self):
        self.order = create_order(status='PENDING')
        self.assertEqual(('SHIPPED', 'CANCELLED'),
                         self.order.available_statuses())

    def test_available_statuses_for_shipped_order(self):
        self.order = create_order(status='SHIPPED')
        self.assertEqual(('COMPLETE',), self.order.available_statuses())

    def test_no_statuses_available_for_no_status(self):
        self.order = create_order()
        self.assertEqual((), self.order.available_statuses())

    def test_set_status_respects_pipeline(self):
        self.order = create_order(status='SHIPPED')
        with self.assertRaises(InvalidOrderStatus):
            self.order.set_status('PENDING')

    def test_set_status_does_nothing_for_same_status(self):
        self.order = create_order(status='PENDING')
        self.order.set_status('PENDING')
        self.assertEqual('PENDING', self.order.status)

    def test_set_status_works(self):
        self.order = create_order(status='PENDING')
        self.order.set_status('SHIPPED')
        self.assertEqual('SHIPPED', self.order.status)

    def test_cascading_status_change(self):
        self.order = create_order(status='PENDING')
        self.order.set_status('SHIPPED')
        for line in self.order.lines.all():
            self.assertEqual('SHIPPED', line.status)


class OrderNoteTests(TestCase):

    def setUp(self):
        self.order = create_order()

    def test_system_notes_are_not_editable(self):
        note = self.order.notes.create(note_type=OrderNote.SYSTEM, message='test')
        self.assertFalse(note.is_editable())

    def test_non_system_notes_are_editable(self):
        note = self.order.notes.create(message='test')
        self.assertTrue(note.is_editable())

    def test_notes_are_not_editable_after_timeout(self):
        OrderNote.editable_lifetime = 1
        note = self.order.notes.create(message='test')
        self.assertTrue(note.is_editable())

        now = timezone.now()
        with mock.patch.object(timezone, 'now') as mock_timezone:
            mock_timezone.return_value = now + timedelta(seconds=30)
            self.assertFalse(note.is_editable())


class LineTests(TestCase):

    def setUp(self):
        basket = Basket()
        basket.add_product(create_product(price=D('10.00')), 4)
        self.order = create_order(number='100002', basket=basket)
        self.line = self.order.lines.all()[0]
        self.order_placed,_ = ShippingEventType.objects.get_or_create(code='order_placed',
                                                                      name='Order placed')
        self.dispatched,_ = ShippingEventType.objects.get_or_create(code='dispatched',
                                                                    name='Dispatched')

    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def event(self, type, quantity=None):
        """
        Creates a shipping event for the test line
        """
        event = ShippingEvent.objects.create(order=self.order, event_type=type)
        if quantity == None:
            quantity = self.line.quantity
        ShippingEventQuantity.objects.create(event=event, line=self.line, quantity=quantity)

    def test_shipping_event_history(self):
        self.event(self.order_placed, 3)
        self.event(self.dispatched, 1)
        history = self.line.shipping_event_breakdown()
        self.assertEqual(3, history['Order placed']['quantity'])
        self.assertEqual(1, history['Dispatched']['quantity'])

    def test_shipping_status_is_empty_to_start_with(self):
        self.assertEquals('', self.line.shipping_status)

    def test_shipping_status_after_full_line_event(self):
        self.event(self.order_placed)
        self.assertEquals(self.order_placed.name, self.line.shipping_status)

    def test_shipping_status_after_two_full_line_events(self):
        type1 = self.order_placed
        self.event(type1)
        type2 = self.dispatched
        self.event(type2)
        self.assertEquals(type2.name, self.line.shipping_status)

    def test_shipping_status_after_partial_line_event(self):
        type = self.order_placed
        self.event(type, 3)
        expected = "%s (%d/%d items)" % (type.name, 3, self.line.quantity)
        self.assertEquals(expected, self.line.shipping_status)

    def test_has_passed_shipping_status_after_full_line_event(self):
        type = self.order_placed
        self.event(type)
        self.assertTrue(self.line.has_shipping_event_occurred(type))

    def test_has_passed_shipping_status_after_partial_line_event(self):
        type = self.order_placed
        self.event(type, self.line.quantity - 1)
        self.assertFalse(self.line.has_shipping_event_occurred(type), 1)

    def test_has_passed_shipping_status_after_multiple_line_event(self):
        event_types = [ShippingEventType.objects.get(code='order_placed'),
                       ShippingEventType.objects.get(code='dispatched')]
        for type in event_types:
            self.event(type)
        for type in event_types:
            self.assertTrue(self.line.has_shipping_event_occurred(type))

    def test_inconsistent_shipping_status_setting(self):
        type = self.order_placed
        self.event(type, self.line.quantity - 1)

        with self.assertRaises(ValueError):
            self.event(type, self.line.quantity)

    def test_inconsistent_shipping_quantities(self):
        type = ShippingEventType.objects.get(code='order_placed')
        self.event(type, self.line.quantity - 1)

        with self.assertRaises(ValueError):
            # Total quantity is too high
            self.event(type, 2)


class LineStatusTests(TestCase):

    def setUp(self):
        Line.pipeline = {'A': ('B', 'C'),
                         'B': ('C',)}
        self.order = create_order()
        self.line = self.order.lines.all()[0]
        self.line.status = 'A'
        self.line.save()

    def test_all_statuses_class_method(self):
        self.assertEqual(['A', 'B'], Line.all_statuses())

    def test_invalid_status_set_raises_exception(self):
        with self.assertRaises(InvalidLineStatus):
            self.line.set_status('D')

    def test_set_status_changes_status(self):
        self.line.set_status('C')
        self.assertEqual('C', self.line.status)

    def test_setting_same_status_does_nothing(self):
        self.line.set_status('A')


class ShippingEventTypeTests(TestCase):

    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def test_code_is_set_automatically(self):
        etype = ShippingEventType.objects.create(name='Returned')
        self.assertEqual('returned', etype.code)

    def test_get_prerequisites(self):
        ShippingEventType.objects.create(name='Shipped',
                                         is_required=True,
                                         sequence_number=0)
        etype = ShippingEventType.objects.create(name='Returned',
                                                 is_required=False,
                                                 sequence_number=1)
        prereqs = etype.get_prerequisites()
        self.assertEqual(1, len(prereqs))
        self.assertEqual('Shipped', prereqs[0].name)


class ShippingEventQuantityTests(TestCase):

    def setUp(self):
        basket = Basket()
        basket.add_product(create_product(price=D('10.00')), 4)
        self.order = create_order(number='100002', basket=basket)
        self.line = self.order.lines.all()[0]

        self.shipped,_ = ShippingEventType.objects.get_or_create(name='Shipped',
                                                                 is_required=True,
                                                                 sequence_number=0)
        self.returned,_ = ShippingEventType.objects.get_or_create(name='Returned',
                                                                 is_required=False,
                                                                 sequence_number=1)

    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def test_quantity_defaults_to_all(self):
        event = self.order.shipping_events.create(event_type=self.shipped)
        event_quantity = ShippingEventQuantity.objects.create(event=event, line=self.line)
        self.assertEquals(self.line.quantity, event_quantity.quantity)

    def test_exception_is_raised_if_previous_events_are_not_passed(self):
        event = self.order.shipping_events.create(event_type=self.returned)
        with self.assertRaises(InvalidShippingEvent):
            ShippingEventQuantity.objects.create(event=event,
                                                 line=self.line)

    def test_event_is_created_ok_when_prerequisites_are_met(self):
        shipped_event = self.order.shipping_events.create(event_type=self.shipped)
        ShippingEventQuantity.objects.create(event=shipped_event,
                                             line=self.line)

        event = self.order.shipping_events.create(event_type=self.returned)
        ShippingEventQuantity.objects.create(event=event,
                                             line=self.line,
                                             quantity=1)


class OrderDiscountTests(TestCase):

    def test_creation_without_offer_or_voucher(self):
        order = create_order(number='100002')
        discount = OrderDiscount.objects.create(order=order, amount=D('10.00'))
        self.assertTrue(discount.voucher is None)
        self.assertTrue(discount.offer is None)

    def test_creation_with_offer(self):
        offer = create_offer()
        order = create_order(number='100002')
        discount = OrderDiscount.objects.create(order=order, amount=D('10.00'),
                                                offer_id=offer.id)
        self.assertEqual(offer.id, discount.offer.id)
