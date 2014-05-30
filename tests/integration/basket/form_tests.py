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


class TestAddToBasketForm(TestCase):

    def test_allows_a_product_quantity_to_be_increased(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertTrue(form.is_valid())

    def test_checks_whether_passed_product_id_matches_a_real_product(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {'quantity': -1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())

    def test_checks_if_purchase_is_permitted(self):
        basket = factories.BasketFactory()
        product = factories.ProductFactory()

        # Build a 4-level mock monster so we can force the return value of
        # whether the product is available to buy. This is a serious code smell
        # and needs to be remedied.
        info = mock.Mock()
        info.availability = mock.Mock()
        info.availability.is_purchase_permitted = mock.Mock(
            return_value=(False, "Not on your nelly!"))
        basket.strategy.fetch_for_product = mock.Mock(
            return_value=info)

        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual('Not on your nelly!', form.errors['__all__'][0])

    def test_mixed_currency_baskets_are_not_permitted(self):
        # Ensure basket is one currency
        basket = mock.Mock()
        basket.currency = 'GBP'
        basket.num_items = 1

        # Ensure new product has different currency
        info = mock.Mock()
        info.price.currency = 'EUR'
        basket.strategy.fetch_for_product = mock.Mock(
            return_value=info)

        product = factories.ProductFactory()

        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
