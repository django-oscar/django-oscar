import datetime
from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.payment.models import Bankcard, Source
from oscar.core.compat import get_user_model
from oscar.test import factories


class TestBankcard(TestCase):

    def test_obfuscates_number_before_saving(self):
        bankcard = Bankcard(number="1000011100000004")
        bankcard.prepare_for_save()
        self.assertEqual("XXXX-XXXX-XXXX-0004", bankcard.number)

    def test_determines_bankcard_type(self):
        bankcard = Bankcard(number="5500000000000004")
        self.assertEqual("Mastercard", bankcard.card_type)

    def test_provides_start_month_property(self):
        start = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard(start_date=start)
        self.assertEqual("01/10", bankcard.start_month())

    def test_provides_end_month_property(self):
        end = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard(expiry_date=end)
        self.assertEqual("01/10", bankcard.expiry_month())

    def test_bankcard_card_correct_save(self):
        # issue #1486
        user_klass = get_user_model()
        user = user_klass.objects.create_user('_', 'a@a.com', 'pwd')
        end = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard.objects.create(
            user=user, number="5500000000000004", expiry_date=end)
        saved_bankcard = Bankcard.objects.get(id=bankcard.id)
        self.assertEqual('Mastercard', saved_bankcard.card_type)

    def test_cardtype_persists_after_save(self):
        user = factories.UserFactory()
        end = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard(
            user=user, number="5500000000000004", expiry_date=end)
        self.assertEqual('Mastercard', bankcard.card_type)

        bankcard.save()
        self.assertEqual('Mastercard', bankcard.card_type)

        reloaded_bankcard = Bankcard.objects.get(id=bankcard.id)
        self.assertEqual('Mastercard', reloaded_bankcard.card_type)


class TestSource(TestCase):

    def test_calculates_initial_balance_correctly(self):
        source = Source(amount_allocated=D('100'))
        self.assertEqual(D('100'), source.balance)

    def test_calculates_balance_correctly(self):
        source = Source(
            amount_allocated=D('100'),
            amount_debited=D('80'),
            amount_refunded=D('20'))
        self.assertEqual(
            D('100') - D('80') + D('20'), source.balance)

    def test_calculates_amount_for_refund_correctly(self):
        source = Source(
            amount_allocated=D('100'),
            amount_debited=D('80'),
            amount_refunded=D('20'))
        self.assertEqual(
            D('80') - D('20'), source.amount_available_for_refund)


class TestAPaymentSource(TestCase):

    def setUp(self):
        order = factories.create_order()
        self.source = factories.SourceFactory(order=order)

    def test_allocation_doesnt_error(self):
        self.source.allocate(D('100.00'))

    def test_debit_doesnt_error(self):
        self.source.allocate(D('100.00'))
        self.source.debit(D('80.00'))

    def test_full_debit_doesnt_error(self):
        self.source.allocate(D('100.00'))
        self.source.debit()
        self.assertEqual(D('0.00'), self.source.balance)

    def test_refund_doesnt_error(self):
        self.source.allocate(D('100.00'))
        self.source.debit(D('80.00'))
        self.source.refund(D('50.00'))
