from decimal import Decimal as D

from django.utils import unittest
from django.core.exceptions import ValidationError

from oscar.product.models import Item, ItemClass
from oscar.stock.models import Partner, StockRecord


class StockRecordTests(unittest.TestCase):

    def setUp(self):
        item_class,_ = ItemClass.objects.get_or_create(name='Dummy item class')
        p = Item.objects.create(title="Dummy product", item_class=item_class)
        partner,_ = Partner.objects.get_or_create(name='Dummy partner')
        self.record = StockRecord.objects.create(product=p, partner_reference='dummy_ref_123', partner=partner,
                                                 price_excl_tax=D('10.00'))
   
    def test_get_price_incl_tax_defaults_to_no_tax(self):
        self.assertEquals(D('10.00'), self.record.price_incl_tax)
        
    def test_get_price_excl_tax_returns_correct_value(self):
        self.assertEquals(D('10.00'), self.record.price_excl_tax)
        
