import datetime
from decimal import Decimal as D

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module


def get_partner_wrapper(test_partner):
    """
    Returns the appropriate partner wrapper given the partner name
    """
    for partner, class_str in settings.OSCAR_PARTNER_WRAPPERS.items():
        if partner == test_partner:
            bits = class_str.split('.')
            class_name = bits.pop()
            module_str = '.'.join(bits)
            module = import_module(module_str)
            return getattr(module, class_name)()
    return DefaultWrapper()


class DefaultWrapper(object):
    """
    Default stockrecord wrapper
    """
    
    def is_available_to_buy(self, stockrecord):
        return stockrecord.num_in_stock > 0
    
    def availability(self, stockrecord):
        if stockrecord.num_in_stock > 0:
            return _("In stock (%d available)" % stockrecord.num_in_stock)
        return _("Out of stock")
    
    def dispatch_date(self, stockrecord):
        if stockrecord.num_in_stock:
            # Assume next day for in-stock items
            return datetime.date.today() + datetime.timedelta(days=1)
        # Assume one week for out-of-stock items
        return datetime.date.today() + datetime.timedelta(days=7)
    
    def calculate_tax(self, stockrecord):
        return D('0.00')