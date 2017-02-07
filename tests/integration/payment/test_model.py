from decimal import Decimal as D
import datetime

from django.test import TestCase

from oscar.apps.payment.models import Bankcard
from oscar.test import factories


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


class TestBankcard(TestCase):

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
