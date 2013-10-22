from decimal import Decimal as D
import datetime
from django.db.transaction import commit_on_success

from oscar.apps.dashboard.reports.csv_utils import CsvUnicodeReader
from oscar.apps.catalogue import models, categories
from oscar.apps.partner import models as partner_models


class Importer(object):
    """
    Quick and dirty catalogue importer
    """

    def __init__(self, logger):
        self.logger = logger

    @commit_on_success
    def handle(self, product_class_name, filepath):
        product_class = models.ProductClass.objects.get(
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
                product = models.Product.objects.get(
                    upc=upc)
            except models.Product.DoesNotExist:
                product = models.Product(upc=upc)
        else:
            product = models.Product()

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
            models.ProductCategory.objects.get_or_create(
                product=product, category=leaf)

        # Stock record
        if partner:
            partner, __ = partner_models.Partner.objects.get_or_create(
                name=partner)
            try:
                record = partner_models.StockRecord.objects.get(
                    product=product)
            except partner_models.StockRecord.DoesNotExist:
                record = partner_models.StockRecord(
                    product=product)
            record.partner = partner
            record.partner_sku = sku
            record.price_excl_tax = D(price)
            if stock != 'NULL':
                record.num_in_stock = stock
            record.save()
