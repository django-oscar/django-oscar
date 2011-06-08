from logging import LogRecord

from django.test import TestCase

from oscar.test.decorators import dataProvider
from oscar.core.logging.formatters import PciFormatter


class PciFormatterTests(TestCase):

    def setUp(self):
        self.formatter = PciFormatter() 

    def test_a_basic_string_is_unchanged(self):
        msg = 'some string'
        record = self.create_log_record(msg)
        self.assertEquals(msg, self.formatter.format(record))

    bankcard_strings = lambda: [('here is my bankcard 1000010000000007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
                                ('here is my bankcard 1000-0100-0000-0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
                                ('here is my bankcard 1000 0100 0000 0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
                                ('here is my bankcard 10 00 01-00 0-000-0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
                                ]

    @dataProvider(bankcard_strings)
    def test_a_sensitive_strings_are_filtered(self, sensitive, filtered):
        record = self.create_log_record(sensitive)
        self.assertEquals(filtered, self.formatter.format(record))    
        
    def create_log_record(self, msg):
        return LogRecord(name=None, 
                         level=None, 
                         pathname='', 
                         lineno=0,
                         msg=msg, 
                         args=None, 
                         exc_info=None)
        
        
    
