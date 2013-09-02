from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.shipping.methods import Free, FixedPrice
from oscar.apps.shipping.models import OrderAndItemCharges


@attr('shipping')
class TestStandardMethods(TestCase):

    def setUp(self):
        self.non_discount_methods = [
            Free(),
            FixedPrice(D('10.00'), D('10.00')),
            OrderAndItemCharges(price_per_order=D('5.00'),
                                price_per_item=D('1.00'))]

    def test_have_is_discounted_property(self):
        for method in self.non_discount_methods:
            self.assertFalse(method.is_discounted)
