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
