"""
Regression tests for the refund over-payment vulnerability fixed in issue #4580.

Calling Source.refund() with an amount greater than amount_available_for_refund
must raise ValidationError instead of silently inflating amount_refunded.
"""
from decimal import Decimal as D

from django.core import exceptions
from django.test import TestCase

from oscar.test.factories import SourceFactory, create_order


class TestRefundValidation(TestCase):
    def setUp(self):
        order = create_order()
        self.source = SourceFactory(order=order)
        # Set up a realistic debit state: £100 allocated, £80 debited, £10 refunded.
        self.source.allocate(D("100.00"))
        self.source.debit(D("80.00"))
        self.source.refund(D("10.00"))
        # available_for_refund == 80 - 10 == 70

    def test_refund_within_limit_succeeds(self):
        """A refund equal to the available amount must not raise."""
        self.source.refund(D("70.00"))  # should not raise
        self.source.refresh_from_db()
        self.assertEqual(D("80.00"), self.source.amount_refunded)

    def test_refund_exceeding_limit_raises_validation_error(self):
        """Refunding more than debited must raise ValidationError."""
        with self.assertRaises(exceptions.ValidationError):
            self.source.refund(D("71.00"))

    def test_partial_refund_does_not_alter_db_on_failure(self):
        """
        When the refund is rejected the database state must remain unchanged.
        """
        original_refunded = self.source.amount_refunded
        try:
            self.source.refund(D("999.00"))
        except exceptions.ValidationError:
            pass
        self.source.refresh_from_db()
        self.assertEqual(original_refunded, self.source.amount_refunded)

    def test_zero_available_refund_raises_for_any_positive_amount(self):
        """After a full refund, any further refund must be rejected."""
        # Refund everything available
        self.source.refund(D("70.00"))
        with self.assertRaises(exceptions.ValidationError):
            self.source.refund(D("0.01"))

    def test_error_message_is_descriptive(self):
        try:
            self.source.refund(D("999.00"))
            self.fail("Expected ValidationError was not raised")
        except exceptions.ValidationError as exc:
            error_str = str(exc)
            # Ensure the message mentions refund/amount
            self.assertTrue(
                "refund" in error_str.lower() or "amount" in error_str.lower(),
                f"Error message is not descriptive: {error_str}",
            )
