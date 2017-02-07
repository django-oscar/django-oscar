import datetime
from decimal import Decimal as D

from django.test import TestCase
from django.core import exceptions
from django.utils.timezone import utc

from oscar.apps.voucher.models import Voucher
from oscar.core.compat import get_user_model
from oscar.test.factories import OrderFactory, UserFactory, VoucherFactory


START_DATETIME = datetime.datetime(2011, 1, 1).replace(tzinfo=utc)
END_DATETIME = datetime.datetime(2012, 1, 1).replace(tzinfo=utc)
User = get_user_model()


class TestSavingAVoucher(TestCase):

    def test_saves_code_as_uppercase(self):
        voucher = VoucherFactory(
            code='lower',
            start_datetime=START_DATETIME, end_datetime=END_DATETIME)
        self.assertEqual('LOWER', voucher.code)

    def test_verifies_dates_are_sensible(self):
        with self.assertRaises(exceptions.ValidationError):
            voucher = Voucher.objects.create(
                code='lower', start_datetime=END_DATETIME,
                end_datetime=START_DATETIME)
            voucher.clean()


class TestAVoucher(TestCase):

    def setUp(self):
        self.voucher = VoucherFactory(
            start_datetime=START_DATETIME, end_datetime=END_DATETIME)

    def test_is_active_between_start_and_end_dates(self):
        test = datetime.datetime(2011, 6, 10).replace(tzinfo=utc)
        self.assertTrue(self.voucher.is_active(test))

    def test_is_active_on_end_date(self):
        self.assertTrue(self.voucher.is_active(END_DATETIME))

    def test_is_active_on_start_date(self):
        self.assertTrue(self.voucher.is_active(START_DATETIME))

    def test_is_inactive_outside_of_start_and_end_dates(self):
        test = datetime.datetime(2012, 3, 10).replace(tzinfo=utc)
        self.assertFalse(self.voucher.is_active(test))

    def test_increments_total_discount_when_recording_usage(self):
        self.voucher.record_discount({'discount': D('10.00')})
        self.assertEqual(self.voucher.total_discount, D('10.00'))
        self.voucher.record_discount({'discount': D('10.00')})
        self.assertEqual(self.voucher.total_discount, D('20.00'))


class TestMultiuseVoucher(TestCase):

    def setUp(self):
        self.voucher = VoucherFactory(usage=Voucher.MULTI_USE)

    def test_is_available_to_same_user_multiple_times(self):
        user, order = UserFactory(), OrderFactory()
        for i in range(10):
            self.voucher.record_usage(order, user)
            is_voucher_available_to_user, __ = self.voucher.is_available_to_user(user=user)
            self.assertTrue(is_voucher_available_to_user)


class TestOncePerCustomerVoucher(TestCase):

    def setUp(self):
        self.voucher = VoucherFactory(usage=Voucher.ONCE_PER_CUSTOMER)

    def test_is_available_to_a_user_once(self):
        user, order = UserFactory(), OrderFactory()
        is_voucher_available_to_user, __ = self.voucher.is_available_to_user(user=user)
        self.assertTrue(is_voucher_available_to_user)

        self.voucher.record_usage(order, user)
        is_voucher_available_to_user, __ = self.voucher.is_available_to_user(user=user)
        self.assertFalse(is_voucher_available_to_user)

    def test_is_available_to_different_users(self):
        users, order = [UserFactory(), UserFactory()], OrderFactory()
        for user in users:
            is_voucher_available_to_user, __ = self.voucher.is_available_to_user(user=user)
            self.assertTrue(is_voucher_available_to_user)

            self.voucher.record_usage(order, user)
            is_voucher_available_to_user, __ = self.voucher.is_available_to_user(user=user)
            self.assertFalse(is_voucher_available_to_user)
