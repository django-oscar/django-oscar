import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from oscar.apps.payment.models import Bankcard
from oscar.apps.payment.forms import (bankcard_type, VISA, MASTERCARD, AMEX, DISCOVER, 
                                      BankcardNumberField, BankcardExpiryMonthField, luhn)


class BankcardTest(TestCase):
    
    def test_get_obfuscated_number(self):
        bankcard = Bankcard(name="David Winterbottom", number="1000011100000004")
        self.assertEquals("XXXX-XXXX-XXXX-0004", bankcard._get_obfuscated_number())
    
    def test_number_is_anonymised_when_saving(self):
        user = User.objects.create(username='Dummy user')
        expiry_date = datetime.date(year=2012, month=02, day=12)
        bankcard = Bankcard.objects.create(name="David Winterbottom", number="1000011100000004", user=user, expiry_date=expiry_date)
        self.assertEquals("XXXX-XXXX-XXXX-0004", bankcard.number)


class BankcardTypeTest(TestCase):
    
    fixture_data = {
        VISA: ('4111111111111111',),
        MASTERCARD: ('5500000000000004',),
        DISCOVER: ('6011000000000004',),
        AMEX: ('340000000000009',),
    }
    
    def test_bankcard_type_sniffer(self):
        for type, numbers in self.fixture_data.items():
            for n in numbers:
                self.assertEquals(type, bankcard_type(n), "%s is a %s" % (n, type))
        

class BankcardNumberFieldTest(TestCase):
    
    def setUp(self):
        self.f = BankcardNumberField()
        
    def test_spaces_are_stipped(self):
        self.assertEquals('4111111111111111', self.f.clean('  4111 1111 1111 1111'))
        

class LuhnTest(TestCase):
    
    valid_numbers = ['4111111111111111',
                     '5500000000000004',
                     '6011000000000004',
                     '340000000000009']
    
    # Tweaked versions of above valid numbers
    invalid_numbers = ['4111111111111110',
                     '5500000000000009',
                     '6011000000000000',
                     '340000000000005']
    
    def test_valid_numbers_pass(self):
        for number in self.valid_numbers:
            self.assertTrue(luhn(number))
            
    def test_invalid_numbers_fail(self):
        for number in self.invalid_numbers:
            self.assertFalse(luhn(number))
    
    