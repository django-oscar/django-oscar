import logging
import os
from decimal import Decimal as D

from django.test import TestCase

from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.exceptions import ImportingError
from oscar.apps.partner.importers import CatalogueImporter
from oscar.apps.partner.models import Partner
from oscar.test.factories import create_product
from tests._site.apps.partner.models import StockRecord

TEST_BOOKS_CSV = os.path.join(os.path.dirname(__file__), "fixtures/books-small.csv")
TEST_BOOKS_SEMICOLON_CSV = os.path.join(
    os.path.dirname(__file__), "fixtures/books-small-semicolon.csv"
)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logger = logging.getLogger("Null")
logger.addHandler(NullHandler())


class CommandEdgeCasesTest(TestCase):
    def setUp(self):
        self.importer = CatalogueImporter(logger)

    def test_sending_no_file_argument_raises_exception(self):
        self.importer.afile = None
        with self.assertRaises(ImportingError):
            self.importer.handle()

    def test_sending_directory_as_file_raises_exception(self):
        self.importer.afile = "/tmp"
        with self.assertRaises(ImportingError):
            self.importer.handle()

    def test_importing_nonexistant_file_raises_exception(self):
        self.importer.afile = "/tmp/catalogue-import.zgvsfsdfsd"
        with self.assertRaises(ImportingError):
            self.importer.handle()


class ImportSmokeTest(TestCase):
    # First row is:
    # "9780115531446","Prepare for Your Practical Driving Test",NULL,"Book","Gardners","9780115531446","10.32","6"
    #
    # Second row is (has no stock data):
    # "9780955337819","Better Photography",NULL,"Book"

    def setUp(self):
        self.importer = CatalogueImporter(logger)
        self.importer.handle(TEST_BOOKS_CSV)
        self.product = Product.objects.get(upc="9780115531446")

    def test_all_rows_are_imported(self):
        self.assertEqual(10, Product.objects.all().count())

    def test_class_is_created(self):
        try:
            ProductClass.objects.get(name="Book")
        except Product.DoesNotExist:
            self.fail()

    def test_only_one_class_is_created(self):
        self.assertEqual(1, ProductClass.objects.all().count())

    def test_item_is_created(self):
        try:
            Product.objects.get(upc="9780115531446")
        except Product.DoesNotExist:
            self.fail()

    def test_title_is_imported(self):
        self.assertEqual("Prepare for Your Practical Driving Test", self.product.title)

    def test_partner_is_created(self):
        try:
            Partner.objects.get(name="Gardners")
        except Product.DoesNotExist:
            self.fail()

    def test_stockrecord_is_created(self):
        try:
            StockRecord.objects.get(partner_sku="9780115531446")
        except Product.DoesNotExist:
            self.fail()

    def test_null_fields_are_skipped(self):
        self.assertEqual("", self.product.description)

    def test_price_is_imported(self):
        stockrecord = self.product.stockrecords.all()[0]
        self.assertEqual(D("10.32"), stockrecord.price)

    def test_num_in_stock_is_imported(self):
        stockrecord = self.product.stockrecords.all()[0]
        self.assertEqual(6, stockrecord.num_in_stock)


class ImportSemicolonDelimitedFileTest(TestCase):
    def setUp(self):
        self.importer = CatalogueImporter(logger, delimiter=";")

    def test_import(self):
        self.importer.handle(TEST_BOOKS_SEMICOLON_CSV)


class ImportWithFlushTest(TestCase):
    def setUp(self):
        self.importer = CatalogueImporter(logger, flush=True)

    def test_items_are_flushed_by_importer(self):
        upc = "0000000000000"
        create_product(price=D("10.00"), upc=upc)

        self.importer.handle(TEST_BOOKS_CSV)

        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(upc=upc)
