VISA, MASTERCARD, AMEX, MAESTRO, DISCOVER = (
    'Visa', 'Mastercard', 'American Express', 'Maestro', 'Discover')


def bankcard_type(number):
    """
    Return the type of a bankcard based on its number.
    """
    number = str(number)
    if len(number) == 13:
        if number[0] == "4":
            return VISA
    elif len(number) == 14:
        if number[:2] == "36":
            return MASTERCARD
    elif len(number) == 15:
        if number[:2] in ("34", "37"):
            return AMEX
    elif len(number) == 16:
        if number[:4] == "6011":
            return DISCOVER
        if number[:2] in ("51", "52", "53", "54", "55"):
            return MASTERCARD
        if number[0] == "4":
            return VISA
    return None


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
