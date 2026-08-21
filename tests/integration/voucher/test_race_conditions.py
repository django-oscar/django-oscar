"""
Race-condition tests for voucher redemption.

These tests verify that concurrent checkouts cannot redeem the same
SINGLE_USE or ONCE_PER_CUSTOMER voucher more than the allowed number of
times (TOCTOU / check-then-act bug).

Strategy
--------
- Use Python threading to fire two ``record_usage`` calls simultaneously.
- The DB-level row-lock (``SELECT FOR UPDATE``) inside the fixed
  ``record_usage`` serialises the threads at the database level.
- Assert that exactly one call succeeds and the second raises
  ``ValidationError`` (voucher already used).

Notes
-----
- ``TransactionTestCase`` is required for the concurrent tests: ``TestCase``
  wraps everything in a single transaction that is never committed, so
  cross-thread DB visibility is impossible.
- Concurrent tests are skipped when SQLite is the backend because SQLite
  does not support ``SELECT FOR UPDATE``.
- The non-concurrent regression tests (``TestSingleUseVoucherAvailabilityCheck``)
  use plain ``TestCase`` and are backend-agnostic.
"""

import threading

from django.core import exceptions
from django.test import TestCase, TransactionTestCase

from oscar.apps.voucher.models import Voucher
from oscar.test.factories import OrderFactory, UserFactory, VoucherFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_sqlite():
    """Return True when the active DB backend is SQLite."""
    from django.db import connection  # lazily imported so DB is set up first

    return connection.vendor == "sqlite"


class _ThreadRunner:
    """
    Run ``fn`` from ``n`` threads simultaneously using a ``threading.Barrier``
    so that all threads enter the target function at roughly the same moment,
    maximising the chance of hitting the race window.
    """

    def __init__(self, fn, n=2):
        self.fn = fn
        self.n = n
        self.errors = []
        self.successes = 0
        self._lock = threading.Lock()
        self._barrier = threading.Barrier(n)

    def _run(self, *args, **kwargs):
        self._barrier.wait()  # All threads start at the same moment
        try:
            self.fn(*args, **kwargs)
            with self._lock:
                self.successes += 1
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self.errors.append(exc)

    def run(self, args_list):
        """
        ``args_list`` – list of ``(args_tuple, kwargs_dict)`` items, one per thread.
        """
        threads = [
            threading.Thread(target=self._run, args=a, kwargs=k) for a, k in args_list
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


# ---------------------------------------------------------------------------
# Non-concurrent regression tests  (TestCase, any DB backend incl. SQLite)
# ---------------------------------------------------------------------------


class TestSingleUseVoucherAvailabilityCheck(TestCase):
    """
    Regression: ``is_available_to_user`` must consult VoucherApplication rows
    (not the cached ``num_orders`` field) for SINGLE_USE vouchers.
    """

    def setUp(self):
        self.voucher = VoucherFactory(usage=Voucher.SINGLE_USE)
        self.user = UserFactory()
        self.order = OrderFactory()

    def test_available_before_first_use(self):
        is_available, _ = self.voucher.is_available_to_user(user=self.user)
        self.assertTrue(is_available)

    def test_unavailable_after_first_use(self):
        self.voucher.record_usage(self.order, self.user)
        self.voucher.refresh_from_db()
        is_available, message = self.voucher.is_available_to_user(user=self.user)
        self.assertFalse(is_available)
        self.assertIn("already been used", str(message))

    def test_record_usage_raises_on_second_attempt(self):
        """``record_usage`` itself must raise ``ValidationError`` on the 2nd call."""
        order2 = OrderFactory()
        self.voucher.record_usage(self.order, self.user)
        with self.assertRaises(exceptions.ValidationError):
            self.voucher.record_usage(order2, self.user)

    def test_stale_num_orders_does_not_bypass_check(self):
        """
        Even if ``num_orders`` is stale (e.g. 0) in an in-memory object,
        ``is_available_to_user`` must refuse a second redemption because it
        queries VoucherApplication rows directly.
        """
        self.voucher.record_usage(self.order, self.user)

        # Simulate a stale in-memory snapshot
        stale = Voucher.objects.get(pk=self.voucher.pk)
        stale.num_orders = 0  # artificially stale

        is_available, _ = stale.is_available_to_user(user=self.user)
        self.assertFalse(
            is_available,
            "Stale num_orders=0 must not bypass the VoucherApplication row check",
        )


# ---------------------------------------------------------------------------
# Concurrent tests  (TransactionTestCase, PostgreSQL / MySQL only)
# ---------------------------------------------------------------------------


class TestSingleUseVoucherRaceCondition(TransactionTestCase):
    """
    Two threads race to redeem the same SINGLE_USE voucher concurrently.
    Exactly one should succeed; the other must receive a ``ValidationError``.

    Skipped automatically on SQLite (no SELECT FOR UPDATE support).
    """

    def setUp(self):
        if _is_sqlite():
            self.skipTest("SELECT FOR UPDATE is not supported by SQLite")
        self.voucher = VoucherFactory(usage=Voucher.SINGLE_USE)
        self.user = UserFactory()
        self.order = OrderFactory()

    def test_concurrent_redemption_allows_only_one_use(self):
        """Two simultaneous redemptions → 1 success, 1 ValidationError."""
        runner = _ThreadRunner(self.voucher.record_usage, n=2)
        runner.run(
            [
                ((self.order, self.user), {}),
                ((self.order, self.user), {}),
            ]
        )

        self.voucher.refresh_from_db()

        self.assertEqual(
            runner.successes,
            1,
            f"Expected exactly 1 successful redemption, got {runner.successes}. "
            f"Errors: {runner.errors}",
        )
        self.assertEqual(
            len(runner.errors),
            1,
            f"Expected exactly 1 ValidationError, got {len(runner.errors)}",
        )
        self.assertIsInstance(runner.errors[0], exceptions.ValidationError)

        # Only one VoucherApplication row must exist
        self.assertEqual(self.voucher.applications.count(), 1)
        self.assertEqual(self.voucher.num_orders, 1)

    def test_sequential_second_redemption_is_rejected(self):
        """Sanity-check: after one successful use, a subsequent call must fail."""
        order2 = OrderFactory()
        self.voucher.record_usage(self.order, self.user)

        with self.assertRaises(exceptions.ValidationError):
            self.voucher.record_usage(order2, self.user)

        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.applications.count(), 1)
        self.assertEqual(self.voucher.num_orders, 1)


class TestOncePerCustomerVoucherRaceCondition(TransactionTestCase):
    """
    Two concurrent redemptions by the *same* authenticated user of a
    ONCE_PER_CUSTOMER voucher must result in exactly one success.
    Two different users must both succeed.

    Skipped automatically on SQLite.
    """

    def setUp(self):
        if _is_sqlite():
            self.skipTest("SELECT FOR UPDATE is not supported by SQLite")
        self.voucher = VoucherFactory(usage=Voucher.ONCE_PER_CUSTOMER)
        self.user = UserFactory()
        self.order = OrderFactory()

    def test_same_user_concurrent_redemption_allows_only_one_use(self):
        """Same user, two concurrent threads → 1 success, 1 ValidationError."""
        runner = _ThreadRunner(self.voucher.record_usage, n=2)
        runner.run(
            [
                ((self.order, self.user), {}),
                ((self.order, self.user), {}),
            ]
        )

        self.voucher.refresh_from_db()

        self.assertEqual(
            runner.successes,
            1,
            f"Expected 1 success for same user, got {runner.successes}. "
            f"Errors: {runner.errors}",
        )
        self.assertEqual(len(runner.errors), 1)
        self.assertIsInstance(runner.errors[0], exceptions.ValidationError)
        self.assertEqual(self.voucher.applications.count(), 1)

    def test_different_users_can_both_redeem(self):
        """
        ONCE_PER_CUSTOMER must allow different users to redeem concurrently.
        Both threads must succeed.
        """
        user2 = UserFactory()
        order2 = OrderFactory()

        runner = _ThreadRunner(self.voucher.record_usage, n=2)
        runner.run(
            [
                ((self.order, self.user), {}),
                ((order2, user2), {}),
            ]
        )

        self.voucher.refresh_from_db()

        self.assertEqual(
            runner.successes,
            2,
            f"Both users should succeed, got {runner.successes} successes. "
            f"Errors: {runner.errors}",
        )
        self.assertEqual(len(runner.errors), 0)
        self.assertEqual(self.voucher.applications.count(), 2)


class TestMultiUseVoucherNoFalseRejections(TransactionTestCase):
    """
    MULTI_USE vouchers must never reject concurrent redemptions.
    The fix must not introduce false negatives for this usage type.

    Skipped automatically on SQLite.
    """

    def setUp(self):
        if _is_sqlite():
            self.skipTest("SELECT FOR UPDATE is not supported by SQLite")
        self.voucher = VoucherFactory(usage=Voucher.MULTI_USE)

    def test_concurrent_redemptions_all_succeed(self):
        """Five simultaneous redemptions of a MULTI_USE voucher must all succeed."""
        n = 5
        users = [UserFactory() for _ in range(n)]
        orders = [OrderFactory() for _ in range(n)]

        results = []
        errors = []
        lock = threading.Lock()
        barrier = threading.Barrier(n)

        def redeem(order, user):
            barrier.wait()
            try:
                self.voucher.record_usage(order, user)
                with lock:
                    results.append(True)
            except Exception as exc:  # noqa: BLE001
                with lock:
                    errors.append(exc)

        threads = [
            threading.Thread(target=redeem, args=(orders[i], users[i]))
            for i in range(n)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.voucher.refresh_from_db()

        self.assertEqual(
            len(results),
            n,
            f"All {n} MULTI_USE redemptions should succeed. Errors: {errors}",
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(self.voucher.applications.count(), n)
        self.assertEqual(self.voucher.num_orders, n)
