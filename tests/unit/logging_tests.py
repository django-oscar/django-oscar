from logging import LogRecord

import nose.tools

from oscar.core.logging.formatters import PciFormatter


data = [
    ('some string', 'some string'),
    ('here is my bankcard 1000010000000007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
    ('here is my bankcard 1000-0100-0000-0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
    ('here is my bankcard 1000 0100 0000 0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
    ('here is my bankcard 10 00 01-00 0-000-0007', 'here is my bankcard XXXX-XXXX-XXXX-XXXX'),
]


def assert_message_filtered_correctly(string, expected):
    formatter = PciFormatter()
    record = LogRecord(
        name=None, level=None, pathname='', lineno=0,
        msg=string, args=None, exc_info=None)
    nose.tools.eq_(formatter.format(record), expected)


def test_pci_formatter():
    """PCI logging formatter """
    for string, expected in data:
        yield assert_message_filtered_correctly, string, expected
