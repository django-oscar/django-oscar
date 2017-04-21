from decimal import Decimal as D
from oscar.core.loading import get_model

from django.test import TestCase

from oscar.test import factories

Partner = get_model('partner', 'Partner')
PartnerAddress = get_model('partner', 'PartnerAddress')
Country = get_model('address', 'Country')


class TestStockRecord(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.stockrecord = factories.create_stockrecord(
            self.product, price_excl_tax=D('10.00'), num_in_stock=10)

    def test_get_price_excl_tax_returns_correct_value(self):
        self.assertEqual(D('10.00'), self.stockrecord.price_excl_tax)

    def test_net_stock_level_with_no_allocation(self):
        self.assertEqual(10, self.stockrecord.net_stock_level)

    def test_net_stock_level_with_allocation(self):
        self.stockrecord.allocate(5)
        self.assertEqual(10 - 5, self.stockrecord.net_stock_level)

    def test_allocated_does_not_alter_num_in_stock(self):
        self.stockrecord.allocate(5)
        self.assertEqual(10, self.stockrecord.num_in_stock)
        self.assertEqual(5, self.stockrecord.num_allocated)

    def test_allocation_handles_null_value(self):
        self.stockrecord.num_allocated = None
        self.stockrecord.allocate(5)

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


class TestPartnerAddress(TestCase):

    def setUp(self):
        self.partner = Partner._default_manager.create(
            name="Dummy partner")
        self.country = Country._default_manager.create(
            iso_3166_1_a2='GB', name="UNITED KINGDOM")
        self.address = PartnerAddress._default_manager.create(
            title="Dr",
            first_name="Barry",
            last_name="Barrington",
            country=self.country,
            postcode="LS1 2HA",
            partner=self.partner)

    def test_can_get_primary_address(self):
        self.assertEqual(self.partner.primary_address, self.address)

    def test_fails_on_two_addresses(self):
        self.address = PartnerAddress._default_manager.create(
            title="Mrs",
            first_name="Jane",
            last_name="Barrington",
            postcode="LS1 2HA",
            country=self.country,
            partner=self.partner)
        self.assertRaises(
            NotImplementedError, getattr, self.partner, 'primary_address')
