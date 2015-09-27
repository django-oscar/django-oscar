import os
from datetime import datetime
from decimal import Decimal as D

from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.core.compat import UnicodeCSVReader
from oscar.core.loading import get_class, get_classes

ImportingError = get_class('partner.exceptions', 'ImportingError')
Partner, StockRecord = get_classes('partner.models', ['Partner',
                                                      'StockRecord'])
ProductClass, Product, Category, ProductCategory = get_classes(
    'catalogue.models', ('ProductClass', 'Product', 'Category',
                         'ProductCategory'))


class CatalogueImporter(object):
    """
    CSV product importer used to built sandbox. Might not work very well
    for anything else.
    """

    _flush = False

    def __init__(self, logger, delimiter=",", flush=False):
        self.logger = logger
        self._delimiter = delimiter
        self._flush = flush

    def handle(self, file_path=None):
        u"""Handles the actual import process"""
        if not file_path:
            raise ImportingError(_("No file path supplied"))
        Validator().validate(file_path)
        if self._flush is True:
            self.logger.info(" - Flushing product data before import")
            self._flush_product_data()
        self._import(file_path)

    def _flush_product_data(self):
        u"""Flush out product and stock models"""
        Product.objects.all().delete()
        ProductClass.objects.all().delete()
        Partner.objects.all().delete()
        StockRecord.objects.all().delete()

    @atomic
    def _import(self, file_path):
        u"""Imports given file"""
        stats = {'new_items': 0,
                 'updated_items': 0}
        row_number = 0
        with UnicodeCSVReader(
                file_path, delimiter=self._delimiter,
                quotechar='"', escapechar='\\') as reader:
            for row in reader:
                row_number += 1
                self._import_row(row_number, row, stats)
        msg = "New items: %d, updated items: %d" % (stats['new_items'],
                                                    stats['updated_items'])
        self.logger.info(msg)

    def _import_row(self, row_number, row, stats):
        if len(row) != 5 and len(row) != 9:
            self.logger.error("Row number %d has an invalid number of fields"
                              " (%d), skipping..." % (row_number, len(row)))
            return
        item = self._create_item(*row[:5], stats=stats)
        if len(row) == 9:
            # With stock data
            self._create_stockrecord(item, *row[5:9], stats=stats)

    def _create_item(self, product_class, category_str, upc, title,
                     description, stats):
        # Ignore any entries that are NULL
        if description == 'NULL':
            description = ''

        # Create item class and item
        product_class, __ \
            = ProductClass.objects.get_or_create(name=product_class)
        try:
            item = Product.objects.get(upc=upc)
            stats['updated_items'] += 1
        except Product.DoesNotExist:
            item = Product()
            stats['new_items'] += 1
        item.upc = upc
        item.title = title
        item.description = description
        item.product_class = product_class
        item.save()

        # Category
        cat = create_from_breadcrumbs(category_str)
        ProductCategory.objects.create(product=item, category=cat)

        return item

    def _create_stockrecord(self, item, partner_name, partner_sku,
                            price_excl_tax, num_in_stock, stats):
        # Create partner and stock record
        partner, _ = Partner.objects.get_or_create(
            name=partner_name)
        try:
            stock = StockRecord.objects.get(partner_sku=partner_sku)
        except StockRecord.DoesNotExist:
            stock = StockRecord()

        stock.product = item
        stock.partner = partner
        stock.partner_sku = partner_sku
        stock.price_excl_tax = D(price_excl_tax)
        stock.num_in_stock = num_in_stock
        stock.save()


class Validator(object):

    def validate(self, file_path):
        self._exists(file_path)
        self._is_file(file_path)
        self._is_readable(file_path)

    def _exists(self, file_path):
        u"""Check whether a file exists"""
        if not os.path.exists(file_path):
            raise ImportingError(_("%s does not exist") % (file_path))

    def _is_file(self, file_path):
        u"""Check whether file is actually a file type"""
        if not os.path.isfile(file_path):
            raise ImportingError(_("%s is not a file") % (file_path))

    def _is_readable(self, file_path):
        u"""Check file is readable"""
        try:
            f = open(file_path, 'r')
            f.close()
        except IOError:
            raise ImportingError(_("%s is not readable") % (file_path))


class DemoSiteImporter(object):
    """
    Another quick and dirty catalogue product importer. Used to built the
    demo site, and most likely not useful outside of it.
    """

    def __init__(self, logger):
        self.logger = logger

    @atomic
    def handle(self, product_class_name, filepath):
        product_class = ProductClass.objects.get(
            name=product_class_name)

        attribute_codes = []
        with UnicodeCSVReader(filepath) as reader:
            for row in reader:
                if row[1] == 'UPC':
                    attribute_codes = row[9:]
                    continue
                self.create_product(product_class, attribute_codes, row)

    def create_product(self, product_class, attribute_codes, row):  # noqa
        (ptype, upc, title, description,
         category, partner, sku, price, stock) = row[0:9]

        # Create product
        is_child = ptype.lower() == 'variant'
        is_parent = ptype.lower() == 'group'

        if upc:
            try:
                product = Product.objects.get(upc=upc)
            except Product.DoesNotExist:
                product = Product(upc=upc)
        else:
            product = Product()

        if is_child:
            product.structure = Product.CHILD
            # Assign parent for children
            product.parent = self.parent
        elif is_parent:
            product.structure = Product.PARENT
        else:
            product.structure = Product.STANDALONE

        if not product.is_child:
            product.title = title
            product.description = description
            product.product_class = product_class

        # Attributes
        if not product.is_parent:
            for code, value in zip(attribute_codes, row[9:]):
                # Need to check if the attribute requires an Option instance
                attr = product_class.attributes.get(
                    code=code)
                if attr.is_option:
                    value = attr.option_group.options.get(option=value)
                if attr.type == 'date':
                    value = datetime.strptime(value, "%d/%m/%Y").date()
                setattr(product.attr, code, value)

        product.save()

        # Save a reference to last parent product
        if is_parent:
            self.parent = product

        # Category information
        if category:
            leaf = create_from_breadcrumbs(category)
            ProductCategory.objects.get_or_create(
                product=product, category=leaf)

        # Stock record
        if partner:
            partner, __ = Partner.objects.get_or_create(name=partner)
            try:
                record = StockRecord.objects.get(product=product)
            except StockRecord.DoesNotExist:
                record = StockRecord(product=product)
            record.partner = partner
            record.partner_sku = sku
            record.price_excl_tax = D(price)
            if stock != 'NULL':
                record.num_in_stock = stock
            record.save()
