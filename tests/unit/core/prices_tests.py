from decimal import Decimal as D

from django.test import TestCase

from oscar.core.prices import Price


class TestPriceObject(TestCase):

    def test_can_be_instantiated_with_tax_amount(self):
        price = Price('USD', D('10.00'), tax=D('2.00'))
        self.assertTrue(price.is_tax_known)
        self.assertEqual(D('12.00'), price.incl_tax)

    def test_can_have_tax_set_later(self):
        price = Price('USD', D('10.00'))
        price.tax = D('2.00')
        self.assertEqual(D('12.00'), price.incl_tax)
