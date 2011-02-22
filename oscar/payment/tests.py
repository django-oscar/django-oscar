import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from oscar.payment.models import Bankcard


class BankcardTest(TestCase):
    
    def test_get_obfuscated_number(self):
        bankcard = Bankcard(name="David Winterbottom", number="1000011100000004")
        self.assertEquals("XXXX-XXXX-XXXX-0004", bankcard._get_obfuscated_number())
    
    def test_number_is_anonymised_when_saving(self):
        user = User.objects.create(username='Dummy user')
        expiry_date = datetime.date(year=2012, month=02, day=12)
        bankcard = Bankcard.objects.create(name="David Winterbottom", number="1000011100000004", user=user, expiry_date=expiry_date)
        self.assertEquals("XXXX-XXXX-XXXX-0004", bankcard.number)

