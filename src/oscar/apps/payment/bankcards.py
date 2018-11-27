VISA, VISA_ELECTRON, MASTERCARD, AMEX, MAESTRO, DISCOVER = (
    'Visa', 'Visa Electron', 'Mastercard', 'American Express',
    'Maestro', 'Discover')
DINERS_CLUB = 'Diners Club'
CHINA_UNIONPAY = 'China UnionPay'
JCB = 'JCB'
LASER = 'Laser'
SOLO = 'Solo'
SWITCH = 'Switch'

# List of (type, lengths, prefixes) tuples
# See http://en.wikipedia.org/wiki/Bank_card_number
CARD_TYPES = [
    (AMEX, (15,), ('34', '37')),
    (CHINA_UNIONPAY, (16, 17, 18, 19), ('62', '88')),
    (DINERS_CLUB, (14,), ('300', '301', '302', '303', '304', '305')),
    (DINERS_CLUB, (14,), ('36',)),
    (DISCOVER, (16,),
     list(map(str, list(range(622126, 622926))))
     + list(map(str, list(range(644, 650)))) + ['6011', '65']),
    (JCB, (16,), list(map(str, list(range(3528, 3590))))),
    (LASER, list(range(16, 20)), ('6304', '6706', '6771', '6709')),
    (MAESTRO, list(range(12, 20)), ('5018', '5020', '5038', '5893', '6304',
                                    '6759', '6761', '6762', '6763', '0604')),
    (MASTERCARD, (16,), list(map(str, list(range(51, 56))))),
    # Diners Club cards match the same pattern as Mastercard.  They are treated
    # as Mastercard normally so we put the mastercard pattern first.
    (DINERS_CLUB, (16,), ('54', '55')),
    (SOLO, list(range(16, 20)), ('6334', '6767')),
    (SWITCH, list(range(16, 20)), ('4903', '4905', '4911', '4936',
                                   '564182', '633110', '6333', '6759')),
    (VISA, (13, 16), ('4',)),
    (VISA_ELECTRON, (16,), ('4026', '417500', '4405', '4508',
                            '4844', '4913', '4917')),
]


def is_amex(number):
    return bankcard_type(number) == AMEX


def bankcard_type(card_number):
    """
    Return the type of a bankcard based on its card_number.

    Returns None is the card_number is not recognised.
    """
    def matches(card_number, lengths, prefixes):
        if len(card_number) not in lengths:
            return False
        for prefix in prefixes:
            if card_number.startswith(prefix):
                return True
        return False
    for card_type, lengths, prefixes in CARD_TYPES:
        if matches(card_number, lengths, prefixes):
            return card_type


def luhn(card_number):
    """
    Test whether a bankcard number passes the Luhn algorithm.
    """
    card_number = str(card_number)
    sum = 0
    num_digits = len(card_number)
    odd_even = num_digits & 1

    for i in range(0, num_digits):
        digit = int(card_number[i])
        if not ((i & 1) ^ odd_even):
            digit = digit * 2
        if digit > 9:
            digit = digit - 9
        sum = sum + digit

    return (sum % 10) == 0
