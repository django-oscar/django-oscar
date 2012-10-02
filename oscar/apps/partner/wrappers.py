from decimal import Decimal as D

from django.utils.translation import ugettext_lazy as _


class DefaultWrapper(object):
    """
    Default stockrecord wrapper
    """
    CODE_IN_STOCK = 'instock'
    CODE_AVAILABLE = 'available'
    CODE_UNAVAILABLE = 'outofstock'

    def is_available_to_buy(self, stockrecord):
        """
        Test whether a product is available to buy.

        This is used to determine whether to show the add-to-basket button.
        """
        if not stockrecord.product.product_class.track_stock:
            return True
        if stockrecord.num_in_stock is None:
            return True
        return stockrecord.net_stock_level > 0

    def is_purchase_permitted(self, stockrecord, user=None, quantity=1):
        """
        Test whether a particular purchase is possible (is a user buying a given
        quantity of the product)
        """
        if not self.is_available_to_buy(stockrecord):
            return False, _("'%s' is not available to purchase") % stockrecord.product.title
        max_qty = self.max_purchase_quantity(stockrecord, user)
        if max_qty is None:
            return True, None
        if max_qty < quantity:
            return False, _("'%(title)s' - A maximum of %(max)d can be bought" %
                            {'title': stockrecord.product.title,
                             'max': max_qty})
        return True, None

    def max_purchase_quantity(self, stockrecord, user=None):
        """
        Return the maximum available purchase quantity for a given user
        """
        if not stockrecord.product.product_class.track_stock:
            return None
        if stockrecord.num_in_stock is None:
            return None
        return stockrecord.net_stock_level

    def availability_code(self, stockrecord):
        """
        Return a code for the availability of this product.

        This is normally used within CSS to add icons to stock messages

        :param oscar.apps.partner.models.StockRecord stockrecord: stockrecord instance
        """
        if stockrecord.net_stock_level > 0:
            return self.CODE_IN_STOCK
        if self.is_available_to_buy(stockrecord):
            return self.CODE_AVAILABLE
        return self.CODE_UNAVAILABLE

    def availability(self, stockrecord):
        """
        Return an availability message for the passed stockrecord.

        :param oscar.apps.partner.models.StockRecord stockrecord: stockrecord instance
        """
        if stockrecord.net_stock_level > 0:
            return _("In stock (%d available)") % stockrecord.net_stock_level
        if self.is_available_to_buy(stockrecord):
            return _('Available')
        return _("Not available")

    def dispatch_date(self, stockrecord):
        """
        We don't provide a default value as it could be confusing.  Subclass
        and override this method to provide estimated dispatch dates
        """
        return None

    def lead_time(self, stockrecord):
        """
        We don't provide a default value as it could be confusing.  Subclass
        and override this method to provide estimated dispatch dates
        """
        return None

    def calculate_tax(self, stockrecord):
        return D('0.00')
