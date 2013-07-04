# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned


class BaseStockRecordController(object):

    # product level
    @property
    def has_stockrecords(self):
        raise NotImplementedError

    def select_stockrecord(self, user=None, quantity=1):
        raise NotImplementedError

    # stock record level
    # basically maps to DefaultWrapper
    @property
    def is_available_to_buy(self):
        raise NotImplementedError

    def is_purchase_permitted(self, user=None, quantity=1):
        raise NotImplementedError

    @property
    def availability_code(self):
        raise NotImplementedError

    @property
    def availability(self):
        raise NotImplementedError

    def max_purchase_quantity(self, user=None):
        raise NotImplementedError

    @property
    def dispatch_date(self):
        raise NotImplementedError

    @property
    def lead_time(self):
        raise NotImplementedError

    @property
    def price_incl_tax(self):
        raise NotImplementedError

    @property
    def price_tax(self):
        raise NotImplementedError


class OneStockRecordController(BaseStockRecordController):

    def __init__(self, product):
        self.product = product

    @property
    def stockrecord(self):
        stockrecords = list(self.product.stockrecords.all())
        if len(stockrecords) == 0:
            return None
        elif len(stockrecords) == 1:
            return stockrecords[0]
        else:
            raise MultipleObjectsReturned(
                "OneStockRecordController operates under the assumption that"
                "only one stock record is available per product")

    @property
    def has_stockrecords(self):
        return self.product.stockrecords.count() >= 1

    # straight mappings
    def select_stockrecord(self, user=None, quantity=1):
        return self.stockrecord

    @property
    def is_available_to_buy(self):
        try:
            return self.stockrecord.is_available_to_buy
        except AttributeError:
            return False

    def is_purchase_permitted(self, user=None, quantity=1):
        try:
            return self.stockrecord.is_purchase_permitted(user, quantity)
        except AttributeError:
            return False

    @property
    def availability_code(self):
        return self.stockrecord.availability_code

    @property
    def availability(self):
        return self.stockrecord.availability

    def max_purchase_quantity(self, user=None):
        return self.stockrecord.max_purchase_quantity(user)

    @property
    def dispatch_date(self):
        return self.stockrecord.dispatch_date

    @property
    def lead_time(self):
        return self.stockrecord.lead_time

    @property
    def price_incl_tax(self):
        return self.stockrecord.price_incl_tax

    @property
    def price_tax(self):
        return self.stockrecord.price_tax


