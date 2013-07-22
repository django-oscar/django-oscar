import datetime

from django.test import TestCase

from oscar.apps.payment.models import Bankcard


class TestBankcard(TestCase):

    def test_obfuscates_number_before_saving(self):
        bankcard = Bankcard(number="1000011100000004")
        bankcard.prepare_for_save()
        self.assertEquals("XXXX-XXXX-XXXX-0004", bankcard.number)

    def test_determines_bankcard_type(self):
        bankcard = Bankcard(number="5500000000000004")
        self.assertEquals("Mastercard", bankcard.card_type)

    def test_provides_start_month_property(self):
        start = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard(start_date=start)
        self.assertEquals("01/10", bankcard.start_month())

    def test_provides_end_month_property(self):
        end = datetime.date(day=1, month=1, year=2010)
        bankcard = Bankcard(expiry_date=end)
        self.assertEquals("01/10", bankcard.expiry_month())
