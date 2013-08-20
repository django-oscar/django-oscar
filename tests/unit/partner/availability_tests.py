from django.test import TestCase

from oscar.apps.partner import availability


class TestBasePolicy(TestCase):

    def setUp(self):
        self.availability = availability.Base()

    def test_does_not_allow_any_purchases(self):
        result, __ = self.availability.is_purchase_permitted(1)
        self.assertFalse(result)

    def test_is_not_available_to_buy(self):
        result = self.availability.is_available_to_buy
        self.assertFalse(result)


class TestUnavailablePolicy(TestCase):

    def setUp(self):
        self.availability = availability.Unavailable()

    def test_is_unavailable(self):
        self.assertFalse(self.availability.is_available_to_buy)

    def test_does_not_allow_any_purchases(self):
        result, __ = self.availability.is_purchase_permitted(1)
        self.assertFalse(result)

    def test_gives_a_reason_for_unavailability(self):
        __, msg = self.availability.is_purchase_permitted(1)
        self.assertEquals("Unavailable", msg)

    def test_returns_availability_code(self):
        self.assertEquals('unavailable', self.availability.code)
