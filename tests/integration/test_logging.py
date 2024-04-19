from logging import LogRecord

from django.test import TestCase

from oscar.core.logging.formatters import PciFormatter


class TestLogging(TestCase):
    data = [
        ("some string", "some string"),
        (
            "here is my bankcard 1000010000000007",
            "here is my bankcard XXXX-XXXX-XXXX-XXXX",
        ),
        (
            "here is my bankcard 1000-0100-0000-0007",
            "here is my bankcard XXXX-XXXX-XXXX-XXXX",
        ),
        (
            "here is my bankcard 1000 0100 0000 0007",
            "here is my bankcard XXXX-XXXX-XXXX-XXXX",
        ),
        (
            "here is my bankcard 10 00 01-00 0-000-0007",
            "here is my bankcard XXXX-XXXX-XXXX-XXXX",
        ),
    ]

    def test_pci_formatter(self):
        """PCI logging formatter"""
        for string, expected in self.data:
            formatter = PciFormatter()
            record = LogRecord(
                name=None,
                level=None,
                pathname="",
                lineno=0,
                msg=string,
                args=None,
                exc_info=None,
            )
            self.assertEqual(formatter.format(record), expected)
