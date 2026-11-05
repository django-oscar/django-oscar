from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TransactionTestCase

from oscar.apps.voucher.models import Voucher
from oscar.test import factories
from oscar.test.utils import run_concurrently


@skipUnless(
    connection.vendor == "postgresql",
    "Concurrent redemptions can only be reproduced on Postgres; SQLite serialises "
    "writers and ignores SELECT FOR UPDATE.",
)
class VoucherLockingTest(TransactionTestCase):
    def setUp(self):
        self.user = factories.UserFactory()

    def redeem_concurrently(self, voucher, num_threads=4):
        def worker():
            voucher.record_usage(factories.OrderFactory(), self.user)

        return run_concurrently(worker, num_threads=num_threads)

    def test_single_use_voucher_is_redeemed_only_once(self):
        voucher = factories.VoucherFactory(usage=Voucher.SINGLE_USE)

        errors = self.redeem_concurrently(voucher)

        self.assertEqual(len(errors), 3)
        for error in errors:
            self.assertIsInstance(error, ValidationError)

        voucher.refresh_from_db()
        self.assertEqual(voucher.applications.count(), 1)
        self.assertEqual(voucher.num_orders, 1)

    def test_once_per_customer_voucher_is_redeemed_only_once_per_customer(self):
        voucher = factories.VoucherFactory(usage=Voucher.ONCE_PER_CUSTOMER)

        errors = self.redeem_concurrently(voucher)

        self.assertEqual(len(errors), 3)
        for error in errors:
            self.assertIsInstance(error, ValidationError)

        voucher.refresh_from_db()
        self.assertEqual(voucher.applications.filter(user=self.user).count(), 1)
        self.assertEqual(voucher.num_orders, 1)
