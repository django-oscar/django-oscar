from decimal import Decimal as D
import datetime
from django.db.transaction import commit_on_success

from oscar.apps.dashboard.reports.csv_utils import CsvUnicodeReader
from oscar.core.loading import get_class
from django.db.models import get_model
from oscar.apps.catalogue import categories

ProductClass = get_model('catalogue', 'ProductClass')
Product = get_model('catalogue', 'Product')
ProductCategory = get_model('catalogue', 'ProductCategory')
StockRecord = get_model('partner', 'StockRecord')
Partner = get_model('partner', 'Partner')


class Importer(object):
    """
    Quick and dirty catalogue importer
    """

    def __init__(self, logger):
        self.logger = logger

    @commit_on_success
    def handle(self, product_class_name, filepath):
        product_class = ProductClass.objects.get(
            name=product_class_name)

        attribute_codes = []
        for row in CsvUnicodeReader(open(filepath, 'r')):
            if row[1] == 'UPC':
                attribute_codes = row[9:]
                continue
            self.create_product(product_class, attribute_codes,  row)

    def create_product(self, product_class, attribute_codes, row):
        ptype, upc, title, description, category, partner, sku, price, stock = row[0:9]

        # Create product
        is_variant = ptype.lower() == 'variant'
        is_group = ptype.lower() == 'group'
        if upc:
            try:
                product = Product.objects.get(
                    upc=upc)
            except Product.DoesNotExist:
                product = Product(upc=upc)
        else:
            product = Product()

        if not is_variant:
            product.title = title
            product.description = description
            product.product_class = product_class

        # Attributes
        if not is_group:
            for code, value in zip(attribute_codes, row[9:]):
                # Need to check if the attribute requires an Option instance
                attr = product_class.attributes.get(
                    code=code)
                if attr.is_option:
                    value = attr.option_group.options.get(option=value)
                if attr.type == 'boolean':
                    value = value == 'T'
                if attr.type == 'date':
                    value = datetime.datetime.strptime(value, "%d/%m/%Y").date()
                setattr(product.attr, code, value)

        # Assign parent for variants
        if is_variant:
            product.parent = self.parent

        product.save()

        # Save a reference to last group product
        if is_group:
            self.parent = product

        # Category information
        if category:
            leaf = categories.create_from_breadcrumbs(category)
            ProductCategory.objects.get_or_create(
                product=product, category=leaf)

        # Stock record
        if partner:
            partner, __ = Partner.objects.get_or_create(
                name=partner)
            try:
                record = StockRecord.objects.get(
                    product=product)
            except StockRecord.DoesNotExist:
                record = StockRecord(
                    product=product)
            record.partner = partner
            record.partner_sku = sku
            record.price_excl_tax = D(price)
            if stock != 'NULL':
                record.num_in_stock = stock
            record.save()
