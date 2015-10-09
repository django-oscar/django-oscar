from django.test import TestCase

from oscar.apps.payment import bankcards


class TestBankCardValidation(TestCase):

    fixture_data = {
        bankcards.VISA: ('4111111111111111',),
        bankcards.MASTERCARD: ('5500000000000004',),
        bankcards.DISCOVER: ('6011000000000004',),
        bankcards.AMEX: ('340000000000009',),
        None: ('1000010000000007',)  # Magic number
    }

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

    def test_bankcard_type_sniffing(self):
        for expected_bankcard_type, numbers in self.fixture_data.items():
            for number in numbers:
                sniffed_bankcard_type = bankcards.bankcard_type(number)
                self.assertEqual(expected_bankcard_type, sniffed_bankcard_type)
    
    def test_valid_numbers(self):
        for number in self.valid_numbers:
            self.assertTrue(bankcards.luhn(number))
    
    def test_invalid_numbers(self):
        for number in self.invalid_numbers:
            self.assertFalse(bankcards.luhn(number))
