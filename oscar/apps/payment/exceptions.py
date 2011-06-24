class PaymentError(Exception):
    pass


class TransactionDeclined(PaymentError):
    pass


class GatewayError(PaymentError):
    pass


class InvalidGatewayRequestError(PaymentError):
    pass


class InsufficientPaymentSources(PaymentError):
    """
    Exception for when a user attempts to checkout without
    specifying enough payment sources to cover the entire order 
    total. 
    
    Eg. When selecting an allocation off a giftcard but not specifying
        a bankcard to take the remainder from.
    """
    pass


class RedirectRequired(PaymentError):
    """
    Exception to be used when payment processsing requires a redirect
    """
    
    def __init__(self, url):
        self.url = url


class UnableToTakePayment(PaymentError):
    """
    Exception to be used for ANTICIPATED payment errors (eg card number wrong, expiry date
    has passed).  The message passed here will be shown to the end user.
    """
    pass
    