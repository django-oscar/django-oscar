from __future__ import unicode_literals

class InvalidStatus(Exception):
    pass


class InvalidOrderStatus(InvalidStatus):
    pass


class InvalidLineStatus(InvalidStatus):
    pass


class InvalidShippingEvent(Exception):
    pass


class InvalidPaymentEvent(Exception):
    pass


class UnableToPlaceOrder(Exception):
    pass
