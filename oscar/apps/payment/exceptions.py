class PaymentException(Exception):
    pass


class TransactionDeclinedException(PaymentException):
    pass


class GatewayException(PaymentException):
    pass


class InvalidGatewayRequestException(PaymentException):
    pass
