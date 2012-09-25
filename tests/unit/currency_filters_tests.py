from decimal import Decimal as D

from django.conf import settings
from django.test import TestCase

from oscar.templatetags.currency_filters import currency


class TestCurrencyFilter(TestCase):

    def test_formats_a_decimal_value_using_oscar_setting(self):
        default = settings.OSCAR_DEFAULT_CURRENCY
        settings.OSCAR_DEFAULT_CURRENCY = u'USD'

        formatted = currency(D('23.54'))
        self.assertEquals(formatted, u'US$23.54')

        # rest to default for further testing
        settings.OSCAR_DEFAULT_CURRENCY = default

    def test_formats_a_decimal_value_using_oscar_default_setting(self):
        formatted = currency(D('23.54'))
        self.assertEquals(formatted, u'£23.54')

    def test_formats_a_string_value_using_oscar_default_setting(self):
        formatted = currency('23.54')
        self.assertEquals(formatted, u'£23.54')

    def test_formats_empty_string_as_empty_value(self):
        formatted = currency('')
        self.assertEquals(formatted, u'')
