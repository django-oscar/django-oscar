import datetime
from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _


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
    
    def lead_time(self, stockrecord):
        return 1
    
    def calculate_tax(self, stockrecord):
        return D('0.00')