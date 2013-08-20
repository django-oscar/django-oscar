from collections import namedtuple
from decimal import Decimal as D

from . import availability, prices


StockInfo = namedtuple('StockInfo', ['price', 'availability', 'stockrecord'])


class Selector(object):
    """
    Responsible for returning the appropriate strategy class for a given
    user/session.

    This can be called in three ways:

        1. Passing a request and user.  This is for determining
        prices/availability for a normal user browsing the site.

        2. Passing just the user.  This is for offline processes that don't
        have a request instance but do know which user to determine prices for.

        3. Passing nothing.  This is for offline processes that don't
        correspond to a specific user.  Eg, determining a price to store in
        Solr's index.
    """
    def strategy(self, request=None, user=None, **kwargs):
        # Default to the backwards-compatible strategry of picking the fist
        # stockrecord.
        return FirstStockRecord(request)


class Base(object):
    """
    Responsible for picking the appropriate pricing and availability wrappers
    for a product
    """

    def __init__(self, request=None):
        self.request = request
        self.user = None
        if request and request.user.is_authenticated():
            self.user = request.user

    def fetch(self, product):
        raise NotImplementedError(
            "A strategy class must define a fetch method "
            "for returning the availability and pricing "
            "information."
        )


class FirstStockRecord(Base):
    """
    Always use the first (normally only) stock record for a product
    """

    def fetch(self, product):
        """
        Return the appropriate product price and availability information for
        this session.
        """
        try:
            record = product.stockrecords.all()[0]
        except IndexError:
            return StockInfo(
                price=prices.Unavailable(),
                availability=availability.Unavailable(),
                stockrecord=None)

        # If we track stock then back-orders aren't allowed
        if not product.get_product_class().track_stock:
            availability_policy = availability.Available()
        else:
            availability_policy = availability.StockRequired(
                record.net_stock_level)

        # Assume zero tax
        pricing_policy = prices.FixedPrice(
            excl_tax=record.price_excl_tax,
            tax=D('0.00'))

        return StockInfo(
            availability=availability_policy,
            price=pricing_policy,
            stockrecord=record)
