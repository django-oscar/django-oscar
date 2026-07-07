import threading
import time
from unittest import skipUnless

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import TransactionTestCase

from oscar.apps.order.models import Order
from oscar.apps.order.utils import OrderCreator
from oscar.core.loading import get_class
from oscar.test import factories
from oscar.test.utils import place_order, run_concurrently

SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")


@skipUnless(
    connection.vendor == "postgresql",
    "A real two-transaction deadlock only happens on Postgres; SQLite serialises "
    "writers, so there is nothing to reproduce there.",
)
class StockRecordDeadlockTest(TransactionTestCase):
    """Show that two concurrent placements which allocate the same stock records
    in opposite line order no longer deadlock, now that ``place_order`` allocates
    in a deterministic (stock-record) order.
    """

    def setUp(self):
        # Two stock records shared by both placements; the test relies on their
        # relative pk order (``sr_low`` has the lower stock-record pk).
        self.product_low = factories.ProductFactory(stockrecords__num_in_stock=1000)
        self.product_high = factories.ProductFactory(stockrecords__num_in_stock=1000)
        self.sr_low = self.product_low.stockrecords.first()
        self.sr_high = self.product_high.stockrecords.first()
        self.assertLess(self.sr_low.pk, self.sr_high.pk)

    def test_simultaneous_placements_do_not_deadlock(self):
        """The fix: several placements run concurrently, each buying the same two
        products but adding them in *opposite* order, so their basket lines (and
        thus the naive allocation order) disagree. ``place_order`` allocates in
        stock-record order, so every transaction takes the row locks in the same
        order and they serialise instead of deadlocking."""
        creator = OrderCreator()
        user = AnonymousUser()

        # Hold each stock lock briefly after acquiring it, so the transactions'
        # lock windows overlap -- without consistent ordering this reliably
        # forms the deadlock cycle;
        org_update = OrderCreator.update_stock_records

        def slow_update(*args, **kwargs):
            org_update(creator, *args, **kwargs)
            time.sleep(0.3)

        creator.update_stock_records = slow_update

        def worker():
            name = threading.current_thread().name
            index = int(name.rsplit("-", 1)[1])
            basket = factories.BasketFactory()
            # Even/odd threads add the two shared products in opposite order.
            if index % 2 == 0:
                basket.add_product(self.product_high)
                basket.add_product(self.product_low)
            else:
                basket.add_product(self.product_low)
                basket.add_product(self.product_high)
            surcharges = SurchargeApplicator().get_applicable_surcharges(basket)
            place_order(
                creator,
                surcharges=surcharges,
                basket=basket,
                order_number=name,
                user=user,
            )

        errors = run_concurrently(worker, num_threads=4)

        self.assertEqual(errors, [], "concurrent placements raised errors")
        self.assertEqual(Order.objects.count(), 4)

        self.sr_low.refresh_from_db()
        self.sr_high.refresh_from_db()
        self.assertEqual(self.sr_low.num_allocated, 4)
        self.assertEqual(self.sr_high.num_allocated, 4)
