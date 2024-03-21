from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.order import exceptions, models
from oscar.apps.order.processing import EventHandler
from oscar.test import factories
from oscar.test.basket import add_product


class TestEventHandler(TestCase):
    def setUp(self):
        self.order = factories.create_order()
        self.handler = EventHandler()
        self.shipped = models.ShippingEventType.objects.create(name="Shipped")
        self.returned = models.ShippingEventType.objects.create(name="Returned")

    def test_creates_shipping_events_correctly(self):
        self.handler.handle_shipping_event(
            self.order, self.shipped, self.order.lines.all(), [1]
        )

        events = self.order.shipping_events.all()
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual("Shipped", event.event_type.name)

    def test_verifies_lines_has_passed_shipping_event(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5)
        order = factories.create_order(basket=basket)

        lines = order.lines.all()
        self.handler.handle_shipping_event(order, self.shipped, lines, [4])

        self.assertTrue(
            self.handler.have_lines_passed_shipping_event(
                order, lines, [3], self.shipped
            )
        )
        self.assertTrue(
            self.handler.have_lines_passed_shipping_event(
                order, lines, [4], self.shipped
            )
        )
        self.assertFalse(
            self.handler.have_lines_passed_shipping_event(
                order, lines, [5], self.shipped
            )
        )

    def test_prevents_event_quantities_higher_than_original_line(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5)
        order = factories.create_order(basket=basket)

        # First shipping event
        lines = order.lines.all()
        self.handler.handle_shipping_event(order, self.shipped, lines, [4])

        with self.assertRaises(exceptions.InvalidShippingEvent):
            self.handler.handle_shipping_event(order, self.shipped, lines, [4])

    def test_are_stock_allocations_available(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)

        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        line = order.lines.get()
        self.assertEqual(
            self.handler.are_stock_allocations_available([line], [line.quantity]),
            True,
        )

        self.assertEqual(
            self.handler.are_stock_allocations_available([line], [105]),
            False,
        )

    def test_are_stock_allocations_available_track_stock_off(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=False
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        line = order.lines.get()
        self.assertEqual(
            self.handler.are_stock_allocations_available([line], [105]),
            True,
        )

    def test_consume_stock_allocations_track_stock_on(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_in_stock = stockrecord.num_in_stock
        num_allocated = stockrecord.num_allocated

        lines = order.lines.all()
        self.handler.consume_stock_allocations(
            order, lines, [line.quantity for line in lines]
        )

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated - 5,
            "Allocated stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_in_stock,
            num_in_stock - 5,
            "Stock should have decreased, but didn't.",
        )

    def test_consume_stock_allocations_track_stock_off(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=False
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_in_stock = stockrecord.num_in_stock
        num_allocated = stockrecord.num_allocated

        lines = order.lines.all()
        self.handler.consume_stock_allocations(
            order, lines, [line.quantity for line in lines]
        )

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated,
            "Allocated stock shouldn't have changed, but it did.",
        )
        self.assertEqual(
            stockrecord.num_in_stock,
            num_in_stock,
            "Stock shouldn't have changed, but it did.",
        )

    def test_consume_stock_allocations_without_line_arguments(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_in_stock = stockrecord.num_in_stock
        num_allocated = stockrecord.num_allocated

        self.handler.consume_stock_allocations(order)

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated - 5,
            "Allocated stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_in_stock,
            num_in_stock - 5,
            "Stock should have decreased, but didn't.",
        )

    def test_line_allocations(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        line = order.lines.get()
        stockrecord = product.stockrecords.get()
        num_in_stock = stockrecord.num_in_stock
        stock_num_allocated = stockrecord.num_allocated

        line.consume_allocation(2)
        line.refresh_from_db(fields=["num_allocated"])
        stockrecord.refresh_from_db(fields=["num_allocated", "num_in_stock"])
        self.assertEqual(
            line.num_allocated,
            3,
            "Allocated line stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_allocated,
            stock_num_allocated - 2,
            "Allocated stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_in_stock,
            num_in_stock - 2,
            "Stock should have decreased, but didn't.",
        )

        line.cancel_allocation(2)
        line.refresh_from_db(fields=["num_allocated", "allocation_cancelled"])
        stockrecord.refresh_from_db(fields=["num_allocated", "num_in_stock"])
        self.assertEqual(line.allocation_cancelled, False)
        self.assertEqual(
            line.num_allocated,
            1,
            "Allocated line stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_allocated,
            stock_num_allocated - 4,
            "Allocated stock should have decreased, but didn't.",
        )
        self.assertEqual(
            stockrecord.num_in_stock,
            num_in_stock - 2,
            "Stock should have decreased, but didn't.",
        )

        line.cancel_allocation(1)
        line.refresh_from_db(fields=["num_allocated", "allocation_cancelled"])
        self.assertEqual(line.allocation_cancelled, True)
        self.assertEqual(
            line.num_allocated,
            0,
            "Allocated line stock should have decreased, but didn't.",
        )

    def test_cancel_stock_allocations_track_stock_on(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_allocated = stockrecord.num_allocated

        lines = order.lines.all()
        self.handler.cancel_stock_allocations(
            order, lines, [line.quantity for line in lines]
        )

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated - 5,
            "Allocated stock should have decreased, but didn't.",
        )

    def test_cancel_stock_allocations_track_stock_off(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=False
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_allocated = stockrecord.num_allocated

        lines = order.lines.all()
        self.handler.cancel_stock_allocations(
            order, lines, [line.quantity for line in lines]
        )

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated,
            "Allocated stock shouldn't have changed, but it did.",
        )

    def test_cancel_stock_allocations_without_line_arguments(self):
        product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=True
        )
        product = factories.ProductFactory(product_class=product_class)
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5, product=product)
        order = factories.create_order(basket=basket)

        stockrecord = product.stockrecords.get()
        num_allocated = stockrecord.num_allocated

        self.handler.cancel_stock_allocations(order)

        stockrecord.refresh_from_db()
        self.assertEqual(
            stockrecord.num_allocated,
            num_allocated - 5,
            "Allocated stock should have decreased, but didn't.",
        )


class TestTotalCalculation(TestCase):
    def setUp(self):
        self.order = factories.create_order()
        self.handler = EventHandler()
        basket = factories.create_basket(empty=True)
        add_product(basket, D("10.00"), 5)
        self.order = factories.create_order(basket=basket)
        self.settled = models.PaymentEventType.objects.create(name="Settled")

    def test_normal_payment_sequence(self):
        # First payment event
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities
        )
        self.assertEqual(2 * D("10.00"), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities
        )

        # Second payment
        line_quantities = [3]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities
        )
        self.assertEqual(3 * D("10.00"), total)

    def test_invalid_payment_sequence(self):
        lines, line_quantities = self.order.lines.all(), [2]
        total = self.handler.calculate_payment_event_subtotal(
            self.settled, lines, line_quantities
        )
        self.assertEqual(2 * D("10.00"), total)
        self.handler.create_payment_event(
            self.order, self.settled, total, lines, line_quantities
        )

        with self.assertRaises(exceptions.InvalidPaymentEvent):
            self.handler.calculate_payment_event_subtotal(
                self.settled, self.order.lines.all(), [4]
            )
