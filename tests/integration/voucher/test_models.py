import datetime
from decimal import Decimal as D

import pytest
from django.core import exceptions
from django.test import TestCase
from django.utils.timezone import utc
from django.utils.translation import gettext_lazy as _

from oscar.apps.voucher.models import Voucher
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.test.factories import (
    ConditionFactory, OrderFactory, RangeFactory, UserFactory, VoucherFactory,
    VoucherSetFactory, create_basket, create_offer, create_product)

START_DATETIME = datetime.datetime(2011, 1, 1).replace(tzinfo=utc)
END_DATETIME = datetime.datetime(2012, 1, 1).replace(tzinfo=utc)
User = get_user_model()
ConditionalOffer = get_model('offer', 'ConditionalOffer')


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


class TestVoucherDelete(TestCase):

    def setUp(self):
        product = create_product(price=100)
        self.offer_range = RangeFactory(products=[product])
        self.offer_condition = ConditionFactory(range=self.offer_range, value=2)

    def test_related_offer_deleted(self):
        # Voucher with offer name corresponding to it as used in the dashboard
        voucher_name = "Voucher"
        voucher = VoucherFactory(name=voucher_name, code="VOUCHER")
        voucher.offers.add(
            create_offer(
                name=_("Offer for voucher '%s'") % voucher_name,
                offer_type='Voucher',
                range=self.offer_range,
                condition=self.offer_condition
            )
        )

        voucher.delete()
        self.assertFalse(
            ConditionalOffer.objects.filter(
                name=_("Offer for voucher '%s'") % voucher_name,
                offer_type=ConditionalOffer.VOUCHER
            ).exists())

    def test_related_offer_different_name_not_deleted(self):
        # Voucher with offer named differently
        voucher = VoucherFactory(name="Voucher", code="VOUCHER")
        voucher.offers.add(
            create_offer(
                name="Different name test",
                offer_type='Voucher',
                range=self.offer_range,
                condition=self.offer_condition
            )
        )

        offer_ids = list(voucher.offers.all().values_list('pk', flat=True))

        voucher.delete()
        count_offers = ConditionalOffer.objects.filter(id__in=offer_ids).count()
        assert len(offer_ids) == count_offers

    def test_related_offer_different_type_not_deleted(self):
        # Voucher with offer not of type "Voucher"
        voucher_name = "Voucher"
        voucher = VoucherFactory(name=voucher_name, code="VOUCHER")
        voucher.offers.add(
            create_offer(
                name=_("Offer for voucher '%s'") % voucher_name,
                offer_type='Site',
                range=self.offer_range,
                condition=self.offer_condition
            )
        )

        offer_ids = list(voucher.offers.all().values_list('pk', flat=True))

        voucher.delete()
        count_offers = ConditionalOffer.objects.filter(id__in=offer_ids).count()
        assert len(offer_ids) == count_offers

    def test_multiple_related_offers_not_deleted(self):
        # Voucher with already used offer
        voucher_name = "Voucher 1"
        offer = create_offer(
            name=_("Offer for voucher '%s'") % voucher_name,
            offer_type='Voucher',
            range=self.offer_range,
            condition=self.offer_condition
        )

        voucher1 = VoucherFactory(name=voucher_name, code="VOUCHER1")
        voucher1.offers.add(offer)

        voucher2 = VoucherFactory(name="Voucher 2", code="VOUCHER2")
        voucher2.offers.add(offer)

        offer_ids = list(voucher1.offers.all().values_list('pk', flat=True))

        voucher1.delete()
        count_offers = ConditionalOffer.objects.filter(id__in=offer_ids).count()
        assert len(offer_ids) == count_offers


class TestAvailableForBasket(TestCase):

    def setUp(self):
        self.basket = create_basket(empty=True)
        self.product = create_product(price=100)
        range = RangeFactory(products=[self.product])
        condition = ConditionFactory(range=range, value=2)
        self.voucher = VoucherFactory()
        self.voucher.offers.add(create_offer(offer_type='Voucher', range=range, condition=condition))

    def test_is_available_for_basket(self):
        self.basket.add_product(product=self.product)
        is_voucher_available_for_basket, __ = self.voucher.is_available_for_basket(self.basket)
        self.assertFalse(is_voucher_available_for_basket)

        self.basket.add_product(product=self.product)
        is_voucher_available_for_basket, __ = self.voucher.is_available_for_basket(self.basket)
        self.assertTrue(is_voucher_available_for_basket)


@pytest.mark.django_db
class TestVoucherSet(object):

    def test_factory(self):
        voucherset = VoucherSetFactory()
        assert voucherset.count == voucherset.vouchers.count()
        code = voucherset.vouchers.first().code
        assert len(code) == 14
        assert code.count('-') == 2
        assert str(voucherset) == voucherset.name
        assert voucherset.offer
        for voucher in voucherset.vouchers.all():
            assert voucherset.offer in voucher.offers.all()

    def test_min_count(self):
        voucherset = VoucherSetFactory(count=20)
        assert voucherset.count == 20
        voucherset.count = 10
        voucherset.save()
        voucherset.refresh_from_db()
        assert voucherset.count == 20

    def test_num_basket_additions(self):
        voucherset = VoucherSetFactory()
        num_additions = voucherset.num_basket_additions
        assert num_additions == 0

    def test_num_orders(self):
        voucherset = VoucherSetFactory()
        assert voucherset.num_orders == 0

        user, order = UserFactory(), OrderFactory()
        voucher = voucherset.vouchers.first()
        voucher.record_usage(order, user)
        assert voucherset.num_orders == 1
