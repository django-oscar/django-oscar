from django.test import TestCase
from django.conf import settings
import mock

from oscar.apps.basket import forms
from oscar.test import factories


class TestBasketLineForm(TestCase):

    def setUp(self):
        self.basket = factories.create_basket()
        self.line = self.basket.all_lines()[0]

    def mock_availability_return_value(self, is_available, reason=''):
        policy = self.line.purchase_info.availability
        policy.is_purchase_permitted = mock.MagicMock(
            return_value=(is_available, reason))

    def build_form(self, quantity=None):
        if quantity is None:
            quantity = self.line.quantity
        return forms.BasketLineForm(
            strategy=self.basket.strategy,
            data={'quantity': quantity},
            instance=self.line)

    def test_enforces_availability_policy_for_valid_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form()
        self.assertTrue(form.is_valid())

    def test_enforces_availability_policy_for_invalid_quantities(self):
        self.mock_availability_return_value(False, "Some reason")
        form = self.build_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['quantity'], ['Some reason'])

    def test_skips_availability_policy_for_zero_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form(quantity=0)
        self.assertTrue(form.is_valid())

    def test_enforces_max_line_quantity(self):
        invalid_qty = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD + 1
        form = self.build_form(quantity=invalid_qty)
        self.assertFalse(form.is_valid())
