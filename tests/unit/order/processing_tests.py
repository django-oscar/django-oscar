from decimal import Decimal as D

from django.test import TestCase
import mock
import six

from oscar.apps.order import processing
from oscar.apps.order import exceptions


class TestValidatePaymentEvent(TestCase):

    def setUp(self):
        self.event_handler = processing.EventHandler()

    def test_valid_lines(self):
        order = mock.Mock()
        lines = [mock.Mock() for r in range(3)]
        line_quantities = [line.quantity for line in lines]
        self.event_handler.validate_payment_event(order, 'pre-auth',
                                                  D('10.00'), lines,
                                                  line_quantities)
        # Has each line has been checked
        for line in lines:
            line.is_payment_event_permitted.assert_called_with('pre-auth',
                                                               line.quantity)

    def test_invalid_lines(self):
        order = mock.Mock()
        invalid_line = mock.Mock()
        invalid_line.is_payment_event_permitted.return_value = False
        invalid_line.id = 6
        lines = [
            mock.Mock(),
            invalid_line,
            mock.Mock(),
        ]
        line_quantities = [line.quantity for line in lines]

        error = "The selected quantity for line #6 is too large"

        with six.assertRaisesRegex(self, exceptions.InvalidPaymentEvent, error):
            self.event_handler.validate_payment_event(order, 'payment',
                                                      D('10.00'), lines,
                                                      line_quantities)

    def test_no_lines(self):
        order = mock.Mock()
        lines = None
        line_quantities = None
        out = self.event_handler.validate_payment_event(
            order, 'payment', D('10.00'), lines, line_quantities)
        self.assertIsNone(out)
