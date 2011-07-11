import os
import csv
import sys
from decimal import Decimal as D

from oscar.core.loading import import_module

import_module('partner.exceptions', ['ImportError'], locals())
import_module('partner.models', ['Partner', 'StockRecord'], locals())
import_module('catalogue.models', ['ProductClass', 'Product'], locals())


class StockImporter(object):
    
    def __init__(self, logger, partner, delimiter):
        self.logger = logger
        self._delimiter = delimiter
        
        try:
            self._partner = Partner.objects.get(name=partner)
        except Partner.DoesNotExist:
            name_list = ", ".join([d['name'] for d in Partner.objects.values('name')])
            raise ImportError("Partner named '%s' does not exist (existing partners: %s)" % (partner, name_list))
        
    def handle(self, file_path=None):
        u"""Handles the actual import process"""
        if not file_path:
            raise ImportError("No file path supplied")
        Validator().validate(file_path)
        self._import(file_path)

    def _import(self, file_path):
        u"""Imports given file"""
        stats = {'updated_items': 0,
                 'unchanged_items': 0,
                 'unmatched_items': 0}
        row_number = 0
        for row in csv.reader(open(file_path, 'rb'), delimiter=self._delimiter, quotechar='"', escapechar='\\'):
            row_number += 1
            self._import_row(row_number, row, stats)
        msg = "\tUpdated items: %d\n\tUnchanged items: %d\n\tUnmatched items: %d" % (
            stats['updated_items'], 
            stats['unchanged_items'],
            stats['unmatched_items'])
        self.logger.info(msg)
    
    def _import_row(self, row_number, row, stats):
        if len(row) != 3:
            self.logger.error("Row number %d has an invalid number of fields, skipping..." % row_number)
        else:
            self._update_stockrecord(*row[:3], row_number=row_number, stats=stats)
    
    def _update_stockrecord(self, partner_sku, price_excl_tax, num_in_stock, row_number, stats):
        try:         
            stock = StockRecord.objects.get(partner=self._partner, partner_sku=partner_sku)
        except StockRecord.DoesNotExist:
            stats['unmatched_items'] += 1
            self.logger.error("\t - Row %d: StockRecord for partner '%s' and sku '%s' does not exist, skipping..." % (row_number, self._partner, partner_sku))
            return
        
        price_changed = False
        if stock.price_excl_tax != D(price_excl_tax):
            stock.price_excl_tax = D(price_excl_tax)
            price_changed = True
            
        stock_changed = False    
        if stock.num_in_stock != int(num_in_stock):
            stock.num_in_stock = num_in_stock
            stock_changed = True
        
        if price_changed or stock_changed:
            stock.save()
            
            msg = " SKU %s:" % (partner_sku)
            if price_changed:
                msg += '\n - Price set to %s' % (price_excl_tax)
            if stock_changed:
                msg += '\n - Stock set to %s' % num_in_stock
            self.logger.info(msg)            
            stats['updated_items'] += 1
        else:
            stats['unchanged_items'] += 1


class CatalogueImporter(object):
    u"""A catalogue importer object"""
    
    _flush = False
    
    def __init__(self, logger, delimiter=",", flush=False):
        self.logger = logger
        self._delimiter = delimiter
        self._flush = flush
        if flush:
            self.logger.info(" - Flushing product data before import")
    
    def handle(self, file_path=None):
        u"""Handles the actual import process"""
        if not file_path:
            raise ImportError("No file path supplied")
        Validator().validate(file_path)
        if self._flush is True:
            self._flush_product_data()
        self._import(file_path)
        
    def _flush_product_data(self):
        u"""Flush out product and stock models"""
        ProductClass.objects.all().delete()
        Product.objects.all().delete()
        Partner.objects.all().delete()
        StockRecord.objects.all().delete()

    def _import(self, file_path):
        u"""Imports given file"""
        stats = {'new_items': 0,
                 'updated_items': 0
                 }
        row_number = 0
        for row in csv.reader(open(file_path,'rb'), delimiter=self._delimiter, quotechar='"', escapechar='\\'):
            row_number += 1
            self._import_row(row_number, row, stats)
        msg = "\tNew items: %d\n\tUpdated items: %d" % (stats['new_items'], stats['updated_items'])
        self.logger.info(msg)
    
    def _import_row(self, row_number, row, stats):
        if len(row) != 4 and len(row) != 8:
            self.logger.error("Row number %d has an invalid number of fields (%d), skipping..." % (row_number, len(row)))
            return
        item = self._create_item(*row[:4], stats=stats)
        if len(row) == 8:
            # With stock data
            self._create_stockrecord(item, *row[4:8], stats=stats)
            
    def _create_item(self, upc, title, description, product_class, stats):
        # Ignore any entries that are NULL
        if description == 'NULL':
            description = ''
        
        # Create item class and item
        product_class,_ = ProductClass.objects.get_or_create(name=product_class)
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
        return item
        
    def _create_stockrecord(self, item, partner_name, partner_sku, price_excl_tax, num_in_stock, stats):            
        # Create partner and stock record
        partner, _ = Partner.objects.get_or_create(name=partner_name)
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
            raise ImportError("%s does not exist" % (file_path))
        
    def _is_file(self, file_path):
        u"""Check whether file is actually a file type"""
        if not os.path.isfile(file_path):
            raise ImportError("%s is not a file" % (file_path))
        
    def _is_readable(self, file_path):
        u"""Check file is readable"""
        try:
            f = open(file_path, 'r')
            f.close()
        except:
            raise ImportError("%s is not readable" % (file_path))