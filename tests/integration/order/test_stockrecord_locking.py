import threading
import time
from unittest import skipUnless

from django.contrib.auth.models import AnonymousUser
from django.db import connection, connections
from django.db.utils import OperationalError
from django.test import TransactionTestCase

from oscar.apps.checkout import calculators
from oscar.apps.order.models import Order
from oscar.apps.order.utils import OrderCreator
from oscar.apps.shipping.methods import Free
from oscar.core.loading import get_class, get_model
from oscar.test import factories

StockRecord = get_model("partner", "StockRecord")
SurchargeApplicator = get_class("checkout.applicator", "SurchargeApplicator")

# Postgres SQLSTATE raised when the server detects a deadlock and kills one of
# the transactions involved.
DEADLOCK_SQLSTATE = "40P01"


def place_order(creator, **kwargs):
    """Place an order without the boilerplate (mirrors test_creator.place_order)."""
    kwargs.setdefault("shipping_method", Free())
    shipping_charge = kwargs["shipping_method"].calculate(kwargs["basket"])
    kwargs["total"] = calculators.OrderTotalCalculator().calculate(
        basket=kwargs["basket"],
        shipping_charge=shipping_charge,
        surcharges=kwargs["surcharges"],
    )
    kwargs["shipping_charge"] = shipping_charge
    return creator.place_order(**kwargs)


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

        errors = self._run_concurrently(worker, num_threads=4)

        deadlocks = [
            error
            for error in errors
            if isinstance(error, OperationalError)
            and getattr(error.__cause__, "pgcode", None) == DEADLOCK_SQLSTATE
        ]
        self.assertEqual(deadlocks, [], "concurrent placements deadlocked")
        self.assertEqual(errors, [], "concurrent placements raised errors")
        self.assertEqual(Order.objects.count(), 4)

    @staticmethod
    def _run_concurrently(fn, num_threads):
        errors = []

        def target():
            try:
                fn()
            except Exception as exc:
                errors.append(exc)
            finally:
                connections.close_all()

        threads = [
            threading.Thread(target=target, name="thread-%d" % i)
            for i in range(num_threads)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        return errors
