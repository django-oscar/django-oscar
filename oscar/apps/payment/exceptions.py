class PaymentException(Exception):
    pass


class TransactionDeclinedException(PaymentException):
    pass


class GatewayException(PaymentException):
    pass


class InvalidGatewayRequestException(PaymentException):
    pass


class RedirectRequiredException(Exception):
    """
    Exception to be used when payment processsing requires a redirect
    """
    
    def __init__(self, url):
        self.url = url


class UnableToTakePaymentException(Exception):
    """
    Exception to be used for ANTICIPATED payment errors (eg card number wrong, expiry date
    has passed).  The message passed here will be shown to the end user.
    """
    pass
    