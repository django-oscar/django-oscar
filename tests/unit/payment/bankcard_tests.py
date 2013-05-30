import nose.tools

from oscar.apps.payment import bankcards


fixture_data = {
    bankcards.VISA: ('4111111111111111',),
    bankcards.MASTERCARD: ('5500000000000004',),
    bankcards.DISCOVER: ('6011000000000004',),
    bankcards.AMEX: ('340000000000009',),
}


def test_bankcard_type_sniffing():

    def compare(number, type):
        nose.tools.eq_(bankcards.bankcard_type(number), type)

    for bankcard_type, numbers in fixture_data.items():
        for number in numbers:
            yield compare, number, bankcard_type


valid_numbers = [
    '4111111111111111',
    '5500000000000004',
    '6011000000000004',
    '340000000000009']

invalid_numbers = [
    '4111111111111110',
    '5500000000000009',
    '6011000000000000',
    '340000000000005']


def test_luhn_check():
    def is_valid(n):
        assert bankcards.luhn(n) is True
    for number in valid_numbers:
        yield is_valid, number

    def is_not_valid(n):
        assert bankcards.luhn(n) is False
    for number in invalid_numbers:
        yield is_not_valid, number
