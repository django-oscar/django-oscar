from unittest import mock

from django.test import TestCase

from oscar.apps.shipping import methods, repository


class TestDefaultShippingRepository(TestCase):
    def setUp(self):
        self.repo = repository.Repository()

    def test_returns_free_when_basket_is_non_empty(self):
        basket = mock.Mock()
        basket.is_shipping_required = mock.Mock(return_value=True)
        basket.has_shipping_discounts = False

        available_methods = self.repo.get_shipping_methods(basket=basket)

        self.assertEqual(1, len(available_methods))
        method = available_methods[0]
        self.assertTrue(isinstance(method, methods.Free))

    def test_returns_no_shipping_required_when_basket_does_not_require_shipping(self):
        basket = mock.Mock()
        basket.is_shipping_required = mock.Mock(return_value=False)
        basket.has_shipping_discounts = False

        available_methods = self.repo.get_shipping_methods(basket=basket)

        self.assertEqual(1, len(available_methods))
        method = available_methods[0]
        self.assertTrue(isinstance(method, methods.NoShippingRequired))

    def test_returns_free_shipping_as_default(self):
        basket = mock.Mock()
        basket.is_shipping_required = mock.Mock(return_value=True)
        basket.has_shipping_discounts = False

        method = self.repo.get_default_shipping_method(basket=basket)

        self.assertTrue(isinstance(method, methods.Free))
