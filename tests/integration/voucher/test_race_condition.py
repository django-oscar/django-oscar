"""
Regression tests for the voucher race condition fixed in issue #4580.

A SINGLE_USE voucher must not be redeemable more than once even when
multiple requests arrive concurrently.  The fix uses SELECT FOR UPDATE
inside an atomic transaction in Voucher.record_usage().
"""
import concurrent.futures

from django.core import exceptions
from django.test import TestCase, TransactionTestCase
from django.db import connection
import unittest

from oscar.apps.voucher.models import Voucher
from oscar.test.factories import (
    OrderFactory,
    UserFactory,
    VoucherFactory,
)


@unittest.skipIf(connection.vendor == 'sqlite', "SQLite does not support concurrent transactions well")
class TestRecordUsageBlocksDuplicateOnSingleUse(TransactionTestCase):
    """
    TransactionTestCase is required here instead of TestCase because we need
    real database commits so that threads can see each other's changes.
    """

    def setUp(self):
        self.voucher = VoucherFactory(usage=Voucher.SINGLE_USE)

    def _apply(self, user_pk):
        """
        Worker function run inside a thread.  Returns True on success,
        False when the expected ValidationError was raised, and re-raises
        anything unexpected.
        """
        from oscar.apps.voucher.models import Voucher as V
        from oscar.core.compat import get_user_model

        User = get_user_model()
        try:
            voucher = V.objects.get(pk=self.voucher.pk)
            user = User.objects.get(pk=user_pk)
            order = OrderFactory()
            voucher.record_usage(order, user)
            return True
        except exceptions.ValidationError:
            return False

    def test_only_one_thread_can_redeem_single_use_voucher(self):
        users = [UserFactory() for _ in range(5)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._apply, u.pk) for u in users]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        successes = sum(1 for r in results if r is True)
        self.assertEqual(
            1,
            successes,
            f"Expected exactly 1 successful redemption, got {successes}",
        )

    def test_only_one_thread_can_redeem_once_per_customer_voucher(self):
        """A ONCE_PER_CUSTOMER voucher must not be redeemable twice by the same user."""
        voucher = VoucherFactory(usage=Voucher.ONCE_PER_CUSTOMER)
        user = UserFactory()

        def _apply():
            from oscar.apps.voucher.models import Voucher as V
            try:
                v = V.objects.get(pk=voucher.pk)
                order = OrderFactory()
                v.record_usage(order, user)
                return True
            except exceptions.ValidationError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(_apply) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        successes = sum(1 for r in results if r is True)
        self.assertEqual(
            1,
            successes,
            f"Expected exactly 1 successful redemption for ONCE_PER_CUSTOMER, got {successes}",
        )


class TestRecordUsageRaisesOnExhaustedSingleUse(TestCase):
    """Sequential (non-threaded) sanity-check: the second call raises."""

    def test_second_usage_raises_validation_error(self):
        voucher = VoucherFactory(usage=Voucher.SINGLE_USE)
        user = UserFactory()
        order1 = OrderFactory()
        order2 = OrderFactory()

        voucher.record_usage(order1, user)

        with self.assertRaises(exceptions.ValidationError):
            voucher.record_usage(order2, user)

    def test_multi_use_voucher_can_be_used_many_times(self):
        """Regression guard: the lock must not break MULTI_USE vouchers."""
        voucher = VoucherFactory(usage=Voucher.MULTI_USE)
        user = UserFactory()
        for _ in range(5):
            order = OrderFactory()
            # Should not raise
            voucher.record_usage(order, user)

        self.assertEqual(5, voucher.num_orders)
