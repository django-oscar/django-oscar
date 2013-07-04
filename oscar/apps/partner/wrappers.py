from decimal import Decimal as D

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.importlib import import_module as django_import_module
from django.db.models import get_model


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
        if stockrecord.num_in_stock is None:
            return True
        return stockrecord.net_stock_level > 0

    def is_purchase_permitted(self, stockrecord, user=None, quantity=1, product=None):
        """
        Test whether a particular purchase is possible (is a user buying a
        given quantity of the product)
        """
        # check, if fetched product is provided, to avoid db call
        product = product or stockrecord.product
        if not self.is_available_to_buy(stockrecord):
            return False, _("'%s' is not available to purchase") % product.title
        max_qty = self.max_purchase_quantity(stockrecord, user, product)
        if max_qty is None:
            return True, None
        if max_qty < quantity:
            return False, _("A maximum of %(max)d can be bought" %
                            {'max': max_qty})
        return True, None

    def max_purchase_quantity(self, stockrecord, user=None, product=None):
        """
        Return the maximum available purchase quantity for a given user
        """
        product = product or stockrecord.product
        if not product.get_product_class().track_stock:
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

    def price_tax(self, stockrecord):
        return D('0.00')


# Cache dict of partner_id => availability wrapper instance
partner_wrappers = None
default_wrapper = DefaultWrapper()


def get_partner_wrapper(partner_id):
    """
    Returns the appropriate partner wrapper given the partner's PK
    """
    if partner_wrappers is None:
        _load_partner_wrappers()
    return partner_wrappers.get(partner_id, default_wrapper)


def _load_partner_wrappers():
    # Prime cache of partner wrapper dict
    global partner_wrappers
    partner_wrappers = {}
    Partner = get_model('partner', 'Partner')
    for code, class_str in settings.OSCAR_PARTNER_WRAPPERS.items():
        try:
            partner = Partner.objects.get(code=code)
        except Partner.DoesNotExist:
            continue
        else:
            module_path, klass = class_str.rsplit('.', 1)
            module = django_import_module(module_path)
            partner_wrappers[partner.id] = getattr(module, klass)()


