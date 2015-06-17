from django.utils.translation import ugettext_lazy as _


class Base(object):
    """
    Base availability policy.
    """

    #: Availability code.  This is used for HTML classes
    code = ''

    #: A description of the availability of a product.  This is shown on the
    #: product detail page.  Eg "In stock", "Out of stock" etc
    message = ''

    #: When this item should be dispatched
    dispatch_date = None

    @property
    def short_message(self):
        """
        A shorter version of the availability message, suitable for showing on
        browsing pages.
        """
        return self.message

    @property
    def is_available_to_buy(self):
        """
        Test if this product is available to be bought.  This is used for
        validation when a product is added to a user's basket.
        """
        # We test a purchase of a single item
        return self.is_purchase_permitted(1)[0]

    def is_purchase_permitted(self, quantity):
        """
        Test whether a proposed purchase is allowed

        Should return a boolean and a reason
        """
        return False, _("unavailable")


# Common availability policies


class Unavailable(Base):
    """
    Policy for when a product is unavailable
    """
    code = 'unavailable'
    message = _("Unavailable")


class Available(Base):
    """
    For when a product is always available, irrespective of stock level.

    This might be appropriate for digital products where stock doesn't need to
    be tracked and the product is always available to buy.
    """
    code = 'available'
    message = _("Available")

    def is_purchase_permitted(self, quantity):
        return True, ""


class StockRequired(Base):
    """
    Allow a product to be bought while there is stock.  This policy is
    instantiated with a stock number (``num_available``).  It ensures that the
    product is only available to buy while there is stock available.

    This is suitable for physical products where back orders (eg allowing
    purchases when there isn't stock available) are not permitted.
    """
    CODE_IN_STOCK = 'instock'
    CODE_OUT_OF_STOCK = 'outofstock'

    def __init__(self, num_available):
        self.num_available = num_available

    def is_purchase_permitted(self, quantity):
        if self.num_available <= 0:
            return False, _("no stock available")
        if quantity > self.num_available:
            msg = _("a maximum of %(max)d can be bought") % {
                'max': self.num_available}
            return False, msg
        return True, ""

    @property
    def code(self):
        if self.num_available > 0:
            return self.CODE_IN_STOCK
        return self.CODE_OUT_OF_STOCK

    @property
    def short_message(self):
        if self.num_available > 0:
            return _("In stock")
        return _("Unavailable")

    @property
    def message(self):
        if self.num_available > 0:
            return _("In stock (%d available)") % self.num_available
        return _("Unavailable")
