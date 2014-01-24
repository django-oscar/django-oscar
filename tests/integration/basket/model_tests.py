from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.basket.models import Basket
from oscar.apps.partner import strategy
from oscar.test import factories
from oscar.apps.catalogue.models import Option


class TestAddingAProductToABasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(
            currency='GBP',
            product=self.product, price_excl_tax=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.product)

    def test_creates_a_line(self):
        self.assertEqual(1, self.basket.num_lines)

    def test_sets_line_prices(self):
        line = self.basket.lines.all()[0]
        self.assertEqual(line.price_incl_tax, self.purchase_info.price.incl_tax)
        self.assertEqual(line.price_excl_tax, self.purchase_info.price.excl_tax)

    def test_means_another_currency_product_cannot_be_added(self):
        product = factories.create_product()
        factories.create_stockrecord(
            currency='USD', product=product, price_excl_tax=D('20.00'))
        with self.assertRaises(ValueError):
            self.basket.add(product)


class TestANonEmptyBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(
            self.product, price_excl_tax=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)
        self.basket.add(self.product, 10)

    def test_can_be_flushed(self):
        self.basket.flush()
        self.assertEqual(self.basket.num_items, 0)

    def test_returns_correct_product_quantity(self):
        self.assertEqual(10, self.basket.product_quantity(
            self.product))

    def test_returns_correct_line_quantity_for_existing_product_and_stockrecord(self):
        self.assertEqual(10, self.basket.line_quantity(
            self.product, self.record))

    def test_returns_zero_line_quantity_for_alternative_stockrecord(self):
        record = factories.create_stockrecord(
            self.product, price_excl_tax=D('5.00'))
        self.assertEqual(0, self.basket.line_quantity(
            self.product, record))

    def test_returns_zero_line_quantity_for_missing_product_and_stockrecord(self):
        product = factories.create_product()
        record = factories.create_stockrecord(
            product, price_excl_tax=D('5.00'))
        self.assertEqual(0, self.basket.line_quantity(
            product, record))

    def test_returns_correct_quantity_for_existing_product_and_stockrecord_and_options(self):
        product = factories.create_product()
        record = factories.create_stockrecord(
            product, price_excl_tax=D('5.00'))
        option = Option.objects.create(name="Message")
        options = [{"option": option, "value": "2"}]

        self.basket.add(product, options=options)
        self.assertEqual(0, self.basket.line_quantity(
            product, record))
        self.assertEqual(1, self.basket.line_quantity(
            product, record, options))


class TestMergingTwoBaskets(TestCase):

    def setUp(self):
        self.product = factories.create_product()
        self.record = factories.create_stockrecord(
            self.product, price_excl_tax=D('10.00'))
        self.purchase_info = factories.create_purchase_info(self.record)

        self.main_basket = Basket()
        self.main_basket.strategy = strategy.Default()
        self.main_basket.add(self.product, quantity=2)

        self.merge_basket = Basket()
        self.merge_basket.strategy = strategy.Default()
        self.merge_basket.add(self.product, quantity=1)

        self.main_basket.merge(self.merge_basket)

    def test_doesnt_sum_quantities(self):
        self.assertEqual(1, self.main_basket.num_lines)

    def test_changes_status_of_merge_basket(self):
        self.assertEqual(Basket.MERGED, self.merge_basket.status)


class TestASubmittedBasket(TestCase):

    def setUp(self):
        self.basket = Basket()
        self.basket.strategy = strategy.Default()
        self.basket.submit()

    def test_has_correct_status(self):
        self.assertTrue(self.basket.is_submitted)

    def test_can_be_edited(self):
        self.assertFalse(self.basket.can_be_edited)
