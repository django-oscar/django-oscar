import datetime
from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _


class DefaultWrapper(object):
    """
    Default stockrecord wrapper
    """
    
    def is_available_to_buy(self, stockrecord):
        if stockrecord.num_in_stock is None:
            return True
        return stockrecord.net_stock_level >= 0

    def is_purchase_permitted(self, stockrecord, user=None, quantity=1):
        if stockrecord.net_stock_level < quantity:
            return False, _("'%s' - A maximum of %d can be bought" % (
                stockrecord.product.title, stockrecord.net_stock_level))
        return True, None

    def availability_code(self, stockrecord):
        """
        Return a code for the availability of this product.

        This is normally used within CSS to add icons to stock messages
        """
        return 'instock' if stockrecord.net_stock_level > 0 else 'outofstock'
    
    def availability(self, stockrecord):
        if stockrecord.net_stock_level > 0:
            return _("In stock (%d available)" % stockrecord.net_stock_level)
        return _("Not available")
    
    def dispatch_date(self, stockrecord):
        if stockrecord.net_stock_level:
            # Assume next day for in-stock items
            return datetime.date.today() + datetime.timedelta(days=1)
        # Assume one week for out-of-stock items
        return datetime.date.today() + datetime.timedelta(days=7)
    
    def lead_time(self, stockrecord):
        return 1
    
    def calculate_tax(self, stockrecord):
        return D('0.00')