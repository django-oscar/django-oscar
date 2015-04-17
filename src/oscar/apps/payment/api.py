from collections import namedtuple


PaymentSource = namedtuple(
    'PaymentSource',
    'type_code type_name currency amount_allocated amount_debited reference')

PaymentEvent = namedtuple(
    'PaymentEvent',
    'type_name amount reference')
