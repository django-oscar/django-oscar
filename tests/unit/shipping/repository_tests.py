from decimal import Decimal as D

from django.test import TestCase
from nose.plugins.attrib import attr

from oscar.apps.basket.models import Basket
from oscar.apps.shipping import repository, methods


@attr('shipping')
class TestShippingRepository(TestCase):

    def setUp(self):
        self.repo = repository.Repository()
        self.basket = Basket()

    def test_returns_free_as_only_option(self):
        available_methods = self.repo.get_shipping_methods(
            user=None, basket=self.basket)
        self.assertEqual(1, len(available_methods))

        method = available_methods[0]
        self.assertTrue(isinstance(method, methods.Free))
        self.assertEqual(D('0.00'), method.charge_incl_tax)
        self.assertEqual(D('0.00'), method.charge_excl_tax)

    def test_allows_free_method_to_be_retrieved(self):
        method = self.repo.find_by_code(methods.Free.code, self.basket)
        self.assertTrue(isinstance(method, methods.Free))

    def test_allows_no_shipping_required_method_to_be_retrieved(self):
        method = self.repo.find_by_code(
            methods.NoShippingRequired.code, self.basket)
        self.assertTrue(isinstance(method, methods.NoShippingRequired))

    def test_returns_none_for_unknown_code(self):
        method = self.repo.find_by_code('asdf', self.basket)
        self.assertIsNone(method)
