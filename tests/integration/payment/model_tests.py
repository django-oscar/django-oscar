from decimal import Decimal as D

from django.test import TestCase
from django_dynamic_fixture import G

from oscar.test import factories
from oscar.apps.payment import models


class TestAPaymentSource(TestCase):

    def setUp(self):
        order = factories.create_order()
        source_type = G(models.SourceType)
        self.source = order.sources.create(
            source_type=source_type)

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
