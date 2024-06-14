# pylint: disable=attribute-defined-outside-init

from datetime import datetime, timedelta
from decimal import Decimal as D
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from oscar.apps.order.exceptions import (
    InvalidLineStatus,
    InvalidOrderStatus,
    InvalidShippingEvent,
)
from oscar.apps.order.models import (
    Line,
    Order,
    OrderDiscount,
    OrderNote,
    ShippingEvent,
    ShippingEventQuantity,
    ShippingEventType,
)
from oscar.apps.order.signals import order_line_status_changed, order_status_changed
from oscar.test.basket import add_product
from oscar.test.contextmanagers import mock_signal_receiver
from oscar.test.factories import (
    OrderFactory,
    OrderLineFactory,
    ShippingAddressFactory,
    ShippingEventFactory,
    create_basket,
    create_offer,
    create_order,
    create_voucher,
)

ORDER_PLACED = "order_placed"


class ShippingAddressTest(TestCase):
    def test_titleless_salutation_is_stripped(self):
        a = ShippingAddressFactory(
            first_name="",
            last_name="Barrington",
            line1="75 Smith Road",
            postcode="N4 8TY",
        )
        self.assertEqual("Barrington", a.salutation)


class OrderStatusPipelineTests(TestCase):
    def setUp(self):
        Order.pipeline = {
            "PENDING": ("SHIPPED", "CANCELLED"),
            "SHIPPED": ("COMPLETE",),
            "COMPLETE": (),
            "CANCELLED": (),
        }
        Order.cascade = {"SHIPPED": "SHIPPED"}

    def tearDown(self):
        Order.pipeline = {}
        Order.cascade = {}

    def test_all_statuses_class_method(self):
        self.assertEqual(
            ["CANCELLED", "COMPLETE", "PENDING", "SHIPPED"],
            sorted(Order.all_statuses()),
        )

    def test_available_statuses_for_pending(self):
        self.order = create_order(status="PENDING")
        self.assertEqual(("SHIPPED", "CANCELLED"), self.order.available_statuses())

    def test_available_statuses_for_shipped_order(self):
        self.order = create_order(status="SHIPPED")
        self.assertEqual(("COMPLETE",), self.order.available_statuses())

    def test_no_statuses_available_for_no_status(self):
        self.order = create_order()
        self.assertEqual((), self.order.available_statuses())

    def test_set_status_respects_pipeline(self):
        self.order = create_order(status="SHIPPED")
        with self.assertRaises(InvalidOrderStatus):
            self.order.set_status("PENDING")

    def test_set_status_does_nothing_for_same_status(self):
        self.order = create_order(status="PENDING")
        self.order.set_status("PENDING")
        self.assertEqual("PENDING", self.order.status)

    def test_set_status_works(self):
        self.order = create_order(status="PENDING")
        self.order.set_status("SHIPPED")
        self.assertEqual("SHIPPED", self.order.status)

    def test_cascading_line_status_not_allowed(self):
        self.order = create_order(status="PENDING")
        self.order.set_status("SHIPPED")
        for line in self.order.lines.all():
            self.assertEqual("a", line.status)

    def test_cascading_status_change_allowed(self):
        Line.pipeline["a"] = ("SHIPPED",)
        self.order = create_order(status="PENDING")
        self.order.set_status("SHIPPED")
        for line in self.order.lines.all():
            self.assertEqual("SHIPPED", line.status)

    def test_set_status_sends_a_signal(self):
        self.order = create_order(status="PENDING")
        with mock_signal_receiver(order_status_changed) as receiver:
            self.order.set_status("SHIPPED")
            self.assertEqual(receiver.call_count, 1)

    def test_set_status_signal_creates_a_order_status_change_object(self):
        self.order = create_order(status="PENDING")
        self.order.set_status("SHIPPED")

        order_status_change = self.order.status_changes.first()

        self.assertEqual(self.order.status_changes.count(), 1)
        self.assertEqual(order_status_change.old_status, "PENDING")
        self.assertEqual(order_status_change.new_status, "SHIPPED")


class OrderNoteTests(TestCase):
    def setUp(self):
        self.order = create_order()

    def test_system_notes_are_not_editable(self):
        note = self.order.notes.create(note_type=OrderNote.SYSTEM, message="test")
        self.assertFalse(note.is_editable())

    def test_non_system_notes_are_editable(self):
        note = self.order.notes.create(message="test")
        self.assertTrue(note.is_editable())

    def test_notes_are_not_editable_after_timeout(self):
        OrderNote.editable_lifetime = 1
        note = self.order.notes.create(message="test")
        self.assertTrue(note.is_editable())

        now = timezone.now()
        with mock.patch.object(timezone, "now") as mock_timezone:
            mock_timezone.return_value = now + timedelta(seconds=30)
            self.assertFalse(note.is_editable())


class LineTests(TestCase):
    def setUp(self):
        basket = create_basket(empty=True)
        add_product(basket, D("10.00"), 4)
        self.order = create_order(number="100002", basket=basket)
        self.line = self.order.lines.all()[0]
        self.order_placed, __ = ShippingEventType.objects.get_or_create(
            code="order_placed", name="Order placed"
        )
        self.dispatched, __ = ShippingEventType.objects.get_or_create(
            code="dispatched", name="Dispatched"
        )

    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def test_is_allocation_consumption_possible_when_num_allocated_is_greater_than_quantity(
        self,
    ):
        self.line.num_allocated = 2

        actual = self.line.is_allocation_consumption_possible(1)

        self.assertTrue(actual)

    def test_is_allocation_consumption_possible_when_num_allocated_is_lower_than_quantity(
        self,
    ):
        self.line.num_allocated = 0

        actual = self.line.is_allocation_consumption_possible(1)

        self.assertFalse(actual)

    def test_is_allocation_consumption_possible_when_num_allocated_is_equal_to_quantity(
        self,
    ):
        self.line.num_allocated = 1

        actual = self.line.is_allocation_consumption_possible(1)

        self.assertTrue(actual)

    def event(self, event_type, quantity=None):
        """
        Creates a shipping event for the test line
        """
        event = ShippingEvent.objects.create(order=self.order, event_type=event_type)
        if quantity is None:
            quantity = self.line.quantity
        ShippingEventQuantity.objects.create(
            event=event, line=self.line, quantity=quantity
        )

    def test_shipping_event_history(self):
        self.event(self.order_placed, 3)
        self.event(self.dispatched, 1)
        history = self.line.shipping_event_breakdown
        self.assertEqual(3, history["Order placed"]["quantity"])
        self.assertEqual(1, history["Dispatched"]["quantity"])

    def test_shipping_status_is_empty_to_start_with(self):
        self.assertEqual("", self.line.shipping_status)

    def test_shipping_status_after_full_line_event(self):
        self.event(self.order_placed)
        self.assertEqual(self.order_placed.name, self.line.shipping_status)

    def test_shipping_status_after_two_full_line_events(self):
        type1 = self.order_placed
        self.event(type1)
        type2 = self.dispatched
        self.event(type2)
        self.assertEqual(type2.name, self.line.shipping_status)

    def test_shipping_status_after_partial_line_event(self):
        event_type = self.order_placed
        self.event(event_type, 3)
        expected = "%s (%d/%d items)" % (event_type.name, 3, self.line.quantity)
        self.assertEqual(expected, self.line.shipping_status)

    def test_has_passed_shipping_status_after_full_line_event(self):
        event_type = self.order_placed
        self.event(event_type)
        self.assertTrue(self.line.has_shipping_event_occurred(event_type))

    def test_has_passed_shipping_status_after_partial_line_event(self):
        event_type = self.order_placed
        self.event(event_type, self.line.quantity - 1)
        self.assertFalse(self.line.has_shipping_event_occurred(event_type), 1)

    def test_has_passed_shipping_status_after_multiple_line_event(self):
        event_types = [
            ShippingEventType.objects.get(code="order_placed"),
            ShippingEventType.objects.get(code="dispatched"),
        ]
        for event_type in event_types:
            self.event(event_type)
        for event_type in event_types:
            self.assertTrue(self.line.has_shipping_event_occurred(event_type))

    def test_inconsistent_shipping_status_setting(self):
        event_type = self.order_placed
        self.event(event_type, self.line.quantity - 1)

        with self.assertRaises(InvalidShippingEvent):
            self.event(event_type, self.line.quantity)

    def test_inconsistent_shipping_quantities(self):
        event_type = ShippingEventType.objects.get(code="order_placed")
        self.event(event_type, self.line.quantity - 1)

        with self.assertRaises(InvalidShippingEvent):
            # Total quantity is too high
            self.event(event_type, 2)

    def test_handles_product_deletion_gracefully(self):
        product = self.line.product
        product.delete()
        line = Line.objects.get(pk=self.line.pk)
        self.assertIsNone(line.product)
        self.assertIsNone(line.stockrecord)
        self.assertEqual(product.title, line.title)
        self.assertEqual(product.upc, line.upc)


class LineStatusTests(TestCase):
    def setUp(self):
        Line.pipeline = {"A": ("B", "C"), "B": ("C",), "C": ()}
        self.order = create_order()
        self.line = self.order.lines.all()[0]
        self.line.status = "A"
        self.line.save()

    def test_all_statuses_class_method(self):
        self.assertEqual(["A", "B", "C"], sorted(Line.all_statuses()))

    def test_invalid_status_set_raises_exception(self):
        with self.assertRaises(InvalidLineStatus):
            self.line.set_status("D")

    def test_set_status_changes_status(self):
        self.line.set_status("C")
        self.assertEqual("C", self.line.status)

    def test_setting_same_status_does_nothing(self):
        self.line.set_status("A")

    def test_set_status_sends_a_signal(self):
        with mock_signal_receiver(order_line_status_changed) as receiver:
            self.line.set_status("C")
            self.assertEqual(receiver.call_count, 1)


class ShippingEventTypeTests(TestCase):
    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def test_code_is_set_automatically(self):
        etype = ShippingEventType.objects.create(name="Returned")
        self.assertEqual("returned", etype.code)


class ShippingEventQuantityTests(TestCase):
    def setUp(self):
        basket = create_basket(empty=True)
        add_product(basket, D("10.00"), 4)
        self.order = create_order(number="100002", basket=basket)
        self.line = self.order.lines.all()[0]

        self.shipped, __ = ShippingEventType.objects.get_or_create(name="Shipped")
        self.returned, __ = ShippingEventType.objects.get_or_create(name="Returned")

    def tearDown(self):
        ShippingEventType.objects.all().delete()

    def test_quantity_defaults_to_all(self):
        event = self.order.shipping_events.create(event_type=self.shipped)
        event_quantity = ShippingEventQuantity.objects.create(
            event=event, line=self.line
        )
        self.assertEqual(self.line.quantity, event_quantity.quantity)

    def test_event_is_created_ok_when_prerequisites_are_met(self):
        shipped_event = self.order.shipping_events.create(event_type=self.shipped)
        ShippingEventQuantity.objects.create(event=shipped_event, line=self.line)

        event = self.order.shipping_events.create(event_type=self.returned)
        ShippingEventQuantity.objects.create(event=event, line=self.line, quantity=1)


class TestOrderDiscount(TestCase):
    def test_can_be_created_without_offer_or_voucher(self):
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(order=order, amount=D("10.00"))

        self.assertTrue(discount.voucher is None)
        self.assertTrue(discount.offer is None)

        self.assertEqual(discount.description(), "")

    def test_can_be_created_with_an_offer(self):
        offer = create_offer()
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order, amount=D("10.00"), offer_id=offer.id
        )
        self.assertEqual(offer.id, discount.offer.id)
        self.assertEqual(offer.name, discount.offer_name)

    def test_can_be_created_with_an_offer_and_specified_offer_name(self):
        offer = create_offer(name="My offer")
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order, amount=D("10.00"), offer_id=offer.id, offer_name="Your offer"
        )
        self.assertEqual(offer.id, discount.offer.id)
        self.assertEqual("Your offer", discount.offer_name)

    def test_can_be_created_with_a_voucher(self):
        voucher = create_voucher()
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order, amount=D("10.00"), voucher_id=voucher.id
        )
        self.assertEqual(voucher.id, discount.voucher.id)
        self.assertEqual(voucher.code, discount.voucher_code)

    def test_can_be_created_with_a_voucher_and_specidied_voucher_code(self):
        voucher = create_voucher()
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order,
            amount=D("10.00"),
            voucher_id=voucher.id,
            voucher_code="anothercode",
        )
        self.assertEqual(voucher.id, discount.voucher.id)
        self.assertEqual("anothercode", discount.voucher_code)

    def test_contains_offer_details_after_offer_is_deleted(self):
        offer = create_offer(name="Get 200% off")
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order, amount=D("10.00"), offer_id=offer.id
        )
        offer.delete()

        self.assertTrue(discount.voucher is None)
        self.assertTrue(discount.offer is None)

        self.assertEqual(discount.description(), "Get 200% off")

    def test_contains_voucher_details_after_voucher_is_deleted(self):
        voucher = create_voucher()
        order = create_order(number="100002")
        discount = OrderDiscount.objects.create(
            order=order, amount=D("10.00"), voucher_id=voucher.id
        )
        voucher.delete()

        self.assertTrue(discount.voucher is None)
        self.assertTrue(discount.offer is None)

        self.assertEqual(discount.description(), voucher.code)


class OrderTests(TestCase):
    @mock.patch("oscar.apps.order.abstract_models.now")
    def test_sets_date_placed_to_now_by_default(self, mock_now):
        tzinfo = timezone.get_current_timezone()
        mock_now.return_value = datetime(2017, 6, 23, 16, 14, tzinfo=tzinfo)
        order = create_order(number="100003")
        self.assertEqual(
            order.date_placed, datetime(2017, 6, 23, 16, 14, tzinfo=tzinfo)
        )

    def test_allows_date_placed_to_be_changed_and_set_explicitly(self):
        order = create_order(number="100003")
        tzinfo = timezone.get_current_timezone()
        order.date_placed = datetime(2012, 8, 11, 16, 14, tzinfo=tzinfo)
        order.save()

        self.assertEqual(
            order.date_placed, datetime(2012, 8, 11, 16, 14, tzinfo=tzinfo)
        )

    def test_shipping_status(self):
        order = OrderFactory()

        line_1 = OrderLineFactory(
            order=order, partner_sku="SKU1234", quantity=2, num_allocated=2
        )
        line_2 = OrderLineFactory(
            order=order, partner_sku="SKU5678", quantity=1, num_allocated=1
        )
        self.assertEqual(order.shipping_status, "")

        event_1 = ShippingEventFactory(order=order, event_type__name="Shipped")
        event_2 = ShippingEventFactory(order=order, event_type__name="Returned")

        # Default status
        self.assertEqual(order.shipping_status, _("In progress"))

        # Set first line to shipped
        event_1.line_quantities.create(line=line_1, quantity=2)
        self.assertEqual(order.shipping_status, _("In progress"))

        # Set first line to returned
        event_2.line_quantities.create(line=line_1, quantity=2)
        self.assertEqual(order.shipping_status, _("In progress"))

        # Set second line to shipped
        event_1.line_quantities.create(line=line_2, quantity=1)
        self.assertEqual(order.shipping_status, _("Shipped"))

        # Set second line to returned
        event_2.line_quantities.create(line=line_2, quantity=1)
        self.assertEqual(order.shipping_status, _("Returned"))

    @override_settings(SECRET_KEY="order_hash_secret")
    def test_verification_hash_generation(self):
        order = OrderFactory(number="111000")
        self.assertEqual(
            order.verification_hash(),
            "111000:Ra7jPGqhkcTm6VXKWEdKtFjA0wBIRVqdxED4bp313os",
        )

    @override_settings(SECRET_KEY="order_hash_secret")
    def test_check_verification_hash_valid(self):
        order = OrderFactory(number="111000")
        self.assertTrue(
            order.check_verification_hash(
                "111000:Ra7jPGqhkcTm6VXKWEdKtFjA0wBIRVqdxED4bp313os"
            )
        )

    @override_settings(SECRET_KEY="order_hash_secret")
    def test_check_verification_hash_invalid_signature(self):
        order = OrderFactory(number="111000")
        self.assertFalse(
            order.check_verification_hash("111000:HKDZWNPLsq7589517c3v1Q6DHKD")
        )

    @override_settings(SECRET_KEY="order_hash_secret")
    def test_check_verification_hash_valid_signature_but_wrong_number(self):
        order = OrderFactory(number="111000")
        # Hash is valid, but it is for a different order number
        self.assertFalse(
            order.check_verification_hash("222000:knvoMB1KAiJu8meWtGce00Y88j4")
        )
