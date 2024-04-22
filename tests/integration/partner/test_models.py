from decimal import Decimal as D

from django.test import TestCase

from oscar.core.loading import get_model
from oscar.test import factories

Partner = get_model("partner", "Partner")
PartnerAddress = get_model("partner", "PartnerAddress")
Country = get_model("address", "Country")


class TestStockRecord(TestCase):
    def setUp(self):
        self.product = factories.create_product()
        self.stockrecord = factories.create_stockrecord(
            self.product, price=D("10.00"), num_in_stock=10
        )

    def test_is_allocation_consumption_possible_when_num_allocated_is_greater_than_quantity(
        self,
    ):
        self.stockrecord.num_allocated = 2

        actual = self.stockrecord.is_allocation_consumption_possible(1)

        self.assertTrue(actual)

    def test_is_allocation_consumption_possible_when_num_allocated_is_lower_than_quantity(
        self,
    ):
        self.stockrecord.num_allocated = 0

        actual = self.stockrecord.is_allocation_consumption_possible(1)

        self.assertFalse(actual)

    def test_is_allocation_consumption_possible_when_num_allocated_is_equal_to_quantity(
        self,
    ):
        self.stockrecord.num_allocated = 1

        actual = self.stockrecord.is_allocation_consumption_possible(1)

        self.assertTrue(actual)

    def test_is_allocation_consumption_possible_when_num_allocated_is_null(self):
        self.stockrecord.num_allocated = None

        actual = self.stockrecord.is_allocation_consumption_possible(1)

        self.assertFalse(actual)

    def test_get_price_excl_tax_returns_correct_value(self):
        self.assertEqual(D("10.00"), self.stockrecord.price)

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


class TestStockRecordNoStockTrack(TestCase):
    def setUp(self):
        self.product_class = factories.ProductClassFactory(
            requires_shipping=False, track_stock=False
        )

    def test_allocate_does_nothing(self):
        product = factories.ProductFactory(product_class=self.product_class)
        stockrecord = factories.create_stockrecord(
            product, price=D("10.00"), num_in_stock=10
        )

        self.assertFalse(stockrecord.can_track_allocations)
        stockrecord.allocate(5)
        self.assertEqual(stockrecord.num_allocated, None)

    def test_allocate_does_nothing_for_child_product(self):
        parent_product = factories.ProductFactory(
            structure="parent", product_class=self.product_class
        )
        child_product = factories.ProductFactory(
            parent=parent_product, product_class=None, structure="child"
        )
        stockrecord = factories.create_stockrecord(
            child_product, price=D("10.00"), num_in_stock=10
        )

        self.assertFalse(stockrecord.can_track_allocations)
        stockrecord.allocate(5)
        self.assertEqual(stockrecord.num_allocated, None)


class TestPartnerAddress(TestCase):
    def setUp(self):
        self.partner = Partner._default_manager.create(name="Dummy partner")
        self.country = Country._default_manager.create(
            iso_3166_1_a2="GB", name="UNITED KINGDOM"
        )
        self.address = PartnerAddress._default_manager.create(
            title="Dr",
            first_name="Barry",
            last_name="Barrington",
            country=self.country,
            postcode="LS1 2HA",
            partner=self.partner,
        )

    def test_can_get_primary_address(self):
        self.assertEqual(self.partner.primary_address, self.address)

    def test_fails_on_two_addresses(self):
        self.address = PartnerAddress._default_manager.create(
            title="Mrs",
            first_name="Jane",
            last_name="Barrington",
            postcode="LS1 2HA",
            country=self.country,
            partner=self.partner,
        )
        self.assertRaises(NotImplementedError, getattr, self.partner, "primary_address")
