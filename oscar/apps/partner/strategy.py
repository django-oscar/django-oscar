from . import availability, prices


class Base(object):
    """
    Responsible for picking the appropriate pricing and availability wrappers
    for a product
    """

    def __init__(self, request):
        self.request = request

    def fetch(self, product):
        pass


class FirstStockrecord(Base):

    def fetch(self, product):
        """
        Return the appropriate product price and availability information for
        this session/user
        """
        try:
            record = product.stockrecords.all()[0]
        except IndexError:
            return {
                'price': prices.NoStockRecord(),
                'availability': availability.NoStockRecord(),
            }
        return {
            'price': prices.WrappedStockrecord(record),
            'availability': availability.WrappedStockrecord(product, record),
            'stockrecord': record,
        }
