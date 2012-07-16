from decimal import Decimal as D
import datetime

from django.test import TestCase

from oscar.test.helpers import create_product
from oscar.apps.partner.abstract_models import partner_wrappers


class DummyWrapper(object):

    def availability(self, stockrecord):
        return 'Dummy response'

    def dispatch_date(self, stockrecord):
        return "Another dummy response"


class StockRecordTests(TestCase):

    def setUp(self):
        self.product = create_product(price=D('10.00'), num_in_stock=10)
        self.stockrecord = self.product.stockrecord

    def test_get_price_incl_tax_defaults_to_no_tax(self):
        self.assertEquals(D('10.00'), self.product.stockrecord.price_incl_tax)

    def test_get_price_excl_tax_returns_correct_value(self):
        self.assertEquals(D('10.00'), self.product.stockrecord.price_excl_tax)

    def test_net_stock_level_with_no_allocation(self):
        self.assertEquals(10, self.product.stockrecord.net_stock_level)

    def test_net_stock_level_with_allocation(self):
        self.product.stockrecord.allocate(5)
        self.assertEquals(10-5, self.product.stockrecord.net_stock_level)

    def test_allocated_does_not_alter_num_in_stock(self):
        self.stockrecord.allocate(5)
        self.assertEqual(10, self.stockrecord.num_in_stock)
        self.assertEqual(5, self.stockrecord.num_allocated)

    def test_consuming_allocation(self):
        self.stockrecord.allocate(5)
        self.stockrecord.consume_allocation(3)
        self.assertEqual(2, self.stockrecord.num_allocated)
        self.assertEqual(7, self.stockrecord.num_in_stock)

    def test_cancelling_allocation(self):
        self.stockrecord.allocate(5)
        self.stockrecord.cancel_allocation(4)
        self.assertEqual(1, self.stockrecord.num_allocated)
        self.assertEqual(10, self.stockrecord.num_in_stock)

    def test_cancelling_allocation_ignores_too_big_allocations(self):
        self.stockrecord.allocate(5)
        self.stockrecord.cancel_allocation(6)
        self.assertEqual(0, self.stockrecord.num_allocated)
        self.assertEqual(10, self.stockrecord.num_in_stock)

    def test_max_purchase_quantity(self):
        self.assertEqual(10, self.stockrecord.max_purchase_quantity())


class DefaultWrapperTests(TestCase):

    def test_default_wrapper_for_in_stock(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=10)
        self.assertEquals("In stock (10 available)", product.stockrecord.availability)
        self.assertEqual("instock", product.stockrecord.availability_code)

    def test_default_wrapper_for_out_of_stock(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=0)
        self.assertEquals(u"Not available",
                          unicode(product.stockrecord.availability))
        self.assertEqual("outofstock", product.stockrecord.availability_code)

    def test_dispatch_date_for_in_stock(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=1)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.assertEquals(tomorrow, product.stockrecord.dispatch_date)

    def test_dispatch_date_for_out_of_stock(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=0)
        date = datetime.date.today() + datetime.timedelta(days=7)
        self.assertEquals(date, product.stockrecord.dispatch_date)


class CustomWrapperTests(TestCase):

    def setUp(self):
        partner_wrappers['Acme'] = DummyWrapper()

    def tearDown(self):
        del partner_wrappers['Acme']

    def test_wrapper_availability_gets_called(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=10)
        self.assertEquals(u"Dummy response", unicode(product.stockrecord.availability))

    def test_wrapper_dispatch_date_gets_called(self):
        product = create_product(price=D('10.00'), partner="Acme", num_in_stock=10)
        self.assertEquals("Another dummy response", product.stockrecord.dispatch_date)
