import mock

from django.test import TestCase

from oscar.apps.checkout.mixins import OrderPlacementMixin


class TestOrderPlacementMixin(TestCase):

    def test_returns_none_when_no_shipping_address_passed_to_creation_method(self):
        address = OrderPlacementMixin().create_shipping_address(
            user=mock.Mock(), shipping_address=None)
        self.assertEqual(address, None)
