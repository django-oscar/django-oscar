import csv
import os
from decimal import Decimal as D

from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

ImportingError = get_class('partner.exceptions', 'ImportingError')

Category = get_model('catalogue', 'Category')
Partner = get_model('partner', 'Partner')
Product = get_model('catalogue', 'Product')
ProductCategory = get_model('catalogue', 'ProductCategory')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')

create_from_breadcrumbs = get_class('catalogue.categories', 'create_from_breadcrumbs')


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
        """Handles the actual import process"""
        if not file_path:
            raise ImportingError(_("No file path supplied"))
        Validator().validate(file_path)
        if self._flush is True:
            self.logger.info(" - Flushing product data before import")
            self._flush_product_data()
        self._import(file_path)

    def _flush_product_data(self):
        """Flush out product and stock models"""
        Product.objects.all().delete()
        ProductClass.objects.all().delete()
        Partner.objects.all().delete()
        StockRecord.objects.all().delete()

    @atomic
    def _import(self, file_path):
        """Imports given file"""
        stats = {'new_items': 0,
                 'updated_items': 0}
        row_number = 0
        with open(file_path, 'rt') as f:
            reader = csv.reader(f, escapechar='\\')
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
        ProductCategory.objects.update_or_create(product=item, category=cat)

        return item

    def _create_stockrecord(self, item, partner_name, partner_sku, price, num_in_stock, stats):
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
        stock.price = D(price)
        stock.num_in_stock = num_in_stock
        stock.save()


class Validator(object):

    def validate(self, file_path):
        self._exists(file_path)
        self._is_file(file_path)
        self._is_readable(file_path)

    def _exists(self, file_path):
        """Check whether a file exists"""
        if not os.path.exists(file_path):
            raise ImportingError(_("%s does not exist") % (file_path))

    def _is_file(self, file_path):
        """Check whether file is actually a file type"""
        if not os.path.isfile(file_path):
            raise ImportingError(_("%s is not a file") % (file_path))

    def _is_readable(self, file_path):
        """Check file is readable"""
        try:
            f = open(file_path, 'r')
            f.close()
        except IOError:
            raise ImportingError(_("%s is not readable") % (file_path))
