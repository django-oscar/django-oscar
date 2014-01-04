import mock

from django.test import TestCase

from oscar.apps.checkout.mixins import OrderPlacementMixin


class TestOrderPlacementMixin(TestCase):

    def test_can_create_shipping_address_for_empty_address(self):
        address = OrderPlacementMixin().create_shipping_address(
            user=mock.Mock(), shipping_address=None)
        self.assertEqual(address, None)
