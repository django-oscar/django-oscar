from django.test import TestCase

from oscar.apps.payment.models import Bankcard


class TestBankcard(TestCase):

    def test_get_obfuscated_number(self):
        bankcard = Bankcard(number="1000011100000004")
        self.assertEquals("XXXX-XXXX-XXXX-0004",
                          bankcard._get_obfuscated_number())
