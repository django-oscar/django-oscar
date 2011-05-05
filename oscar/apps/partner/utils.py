import os
import csv
import sys
from decimal import Decimal as D

from oscar.core.loading import import_module

import_module('partner.exceptions', ['StockImportException'], locals())
import_module('partner.models', ['Partner', 'StockRecord'], locals())

class Importer(object):
    _flush = False
    
    def __init__(self, logger, partner, delimiter):
        self.logger = logger
        self._delimiter = delimiter
        
        try:
            self._partner = Partner.objects.get(name=partner)
        except Partner.DoesNotExist:
            raise StockImportException("Partner named %s does not exist" % partner)
    
    def handle(self, file_path=None):
        u"""Handles the actual import process"""
        if not file_path:
            raise StockImportException("No file path supplied")
        Validator().validate(file_path)
        self._import(file_path)

    def _import(self, file_path):
        u"""Imports given file"""
        stats = {'updated_items': 0}
        row_number = 0
        for row in csv.reader(open(file_path,'rb'), delimiter=self._delimiter, quotechar='"', escapechar='\\'):
            row_number += 1
            self._import_row(row_number, row, stats)
        msg = "Updated items: %d" % (stats['updated_items'])
        self.logger.info(msg)
    
    def _import_row(self, row_number, row, stats):
        if len(row) != 3:
            self.logger.error("Row number %d has an invalid number of fields, skipping..." % row_number)
            return
        self._create_stockrecord(*row[:3], row_number=row_number, stats=stats)
    
    def _create_stockrecord(self, partner_sku, price_excl_tax, num_in_stock, row_number, stats):
        
        try:         
            stock = StockRecord.objects.get(partner=self._partner, partner_sku=partner_sku)
        except StockRecord.DoesNotExist:
            self.logger.error("\t - Row %d: StockRecord for partner '%s' and sku '%s' does not exist, skipping..." % (row_number, self._partner, partner_sku))
            return
        
        stock.price_excl_tax = D(price_excl_tax)
        stock.num_in_stock = num_in_stock
        stock.save()
        
        msg = "  - %d: Partner SKU %s price set to %s, stock set to %s" % (row_number,partner_sku,price_excl_tax,num_in_stock)
        self.logger.info(msg)
        
        stats['updated_items'] += 1
        
class Validator(object):
    def validate(self, file_path):
        self._exists(file_path)
        self._is_file(file_path)
        self._is_readable(file_path)
    
    def _exists(self, file_path):
        u"""Check whether a file exists"""
        if not os.path.exists(file_path):
            raise StockImportException("%s does not exist" % (file_path))
        
    def _is_file(self, file_path):
        u"""Check whether file is actually a file type"""
        if not os.path.isfile(file_path):
            raise StockImportException("%s is not a file" % (file_path))
        
    def _is_readable(self, file_path):
        u"""Check file is readable"""
        try:
            f = open(file_path, 'r')
            f.close()
        except:
            raise StockImportException("%s is not readable" % (file_path))