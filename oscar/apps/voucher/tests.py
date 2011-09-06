import datetime

from django.test import TestCase

from oscar.apps.voucher.models import Voucher


class VoucherTest(TestCase):
    
    def test_is_active(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 01, 10)
        end = datetime.date(2011, 02, 01)
        voucher = Voucher(start_date=start, end_date=end)
        self.assertTrue(voucher.is_active(test))

    def test_is_inactive(self):
        start = datetime.date(2011, 01, 01)
        test = datetime.date(2011, 03, 10)
        end = datetime.date(2011, 02, 01)
        voucher = Voucher(start_date=start, end_date=end)
        self.assertFalse(voucher.is_active(test))
        
    def test_codes_are_saved_as_uppercase(self):
        start = datetime.date(2011, 01, 01)
        end = datetime.date(2011, 02, 01)
        voucher = Voucher(name="Dummy voucher", code="lowercase", start_date=start, end_date=end)
        voucher.save()
        self.assertEquals("LOWERCASE", voucher.code)
        

    
   
