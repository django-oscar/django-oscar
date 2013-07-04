# -*- coding: utf-8 -*-
from django.core.exceptions import MultipleObjectsReturned


class BaseStockRecordController(object):
    """
    This class defines the interface for a stock record controller,
    serving as a base class to inherit from.

    A stock record controller makes the connection between a product and it's
    potentially many stock records. These stock records might be wrapped
    by a partner wrapper.
    It's main task is abstracting away from the potentially many stock records
    and offering a simple interface to inquire about availability of a product.

                                 +----------------+
                                 |Partner  Wrapper|
                                 | +------------+ |
                         +------>| |Stock Record| |
                         |       |.+------------+ |
                         |       +----------------+
                         |       +----------------+
                         |       |Partner  Wrapper|
       +-------+    +---+|       | +------------+ |
       |Product|+-->|SRC|+------>| |Stock Record| |
       +-------+    +---+|       | +------------+ |
                         |       +----------------+
                         |       +----------------+
                         |       |Partner  Wrapper|
                         |       |.+------------+ |
                         +------>| |Stock Record| |
                                 | +------------+ |
                                 +----------------+
    """

    # product level
    @property
    def has_stockrecords(self):
        """
        Test if this product has one or more stock records
        """
        raise NotImplementedError

    def select_stockrecord(self, user=None, quantity=1):
        """
        Select an appropriate stock record for given the constraints
        """
        raise NotImplementedError

    # stock record level

    @property
    def is_available_to_buy(self):
        """
        Test whether one or more stockrecords allow the product to be purchased
        """
        raise NotImplementedError

    def is_purchase_permitted(self, user=None, quantity=1):
        """
        Test whether one or more stock records allow the product to be
        purchased. Optionally allows constraining to a certain user or quantity.

        :param user: Check whether this user is allowed to purchase.
                     None for the general case.
        :param quantity: Check whether the product can be purchased in that
                         quantity.
        :returns: (True, None) or (False, reason) where reason is a
                  human-readable reason as to why it's not possible.
        """
        raise NotImplementedError

    @property
    def availability_code(self):
        """
        Return an product's availability as a code for use in CSS to add icons
        to the overall availability mark-up.
        The default values are "instock", "available" and "unavailable".
        """
        raise NotImplementedError

    @property
    def availability(self):
        """
        Return an availability message that can be displayed to the user.
        For example, "In stock", "Unavailable".
        """
        raise NotImplementedError

    def max_purchase_quantity(self, user=None):
        """
        Return the maximum available purchase quantity

        :param user: Check for a specific user instead of the general case
        """
        raise NotImplementedError

    @property
    def dispatch_date(self):
        """
        Returns an estimated dispatch date or None
        """
        raise NotImplementedError

    @property
    def lead_time(self):
        """
        Returns an estimated lead time or None
        """
        raise NotImplementedError

    @property
    def price_excl_tax(self):
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
    def price_excl_tax(self):
        return self.stockrecord.price_excl_tax

    @property
    def price_incl_tax(self):
        return self.stockrecord.price_incl_tax

    @property
    def price_tax(self):
        return self.stockrecord.price_tax


