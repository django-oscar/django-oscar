from django.test import TestCase

from apps.checkout import forms
from oscar.apps.address import models
from oscar.apps.order import models as order_models


class TestBillingAddressForm(TestCase):

    def setUp(self):
        models.Country.objects.create(
            iso_3166_1_a2='GB', name="Great Britain")
        self.shipping_address = order_models.ShippingAddress()

    def test_selecting_same_as_shipping_is_valid_with_no_billing_address_data(self):
        data = {
            'same_as_shipping': 'same',
            'first_name': '',
            'last_name': '',
            'line1': '',
            'line2': '',
            'line3': '',
            'line4': '',
            'postcode': '',
            'state': '',
            'country': 'GB'
        }
        form = forms.BillingAddressForm(
            shipping_address=self.shipping_address, data=data)
        self.assertTrue(
            form.is_valid(), "Form invalid due to %r" % form.errors)

    def test_selecting_same_as_shipping_is_valid(self):
        data = {
            'same_as_shipping': 'same',
            'first_name': 'test',
            'last_name': 'test',
            'line1': 'test',
            'line2': 'test',
            'line3': 'test',
            'line4': 'test',
            'postcode': 'test',
            'state': '',
            'country': 'GB'
        }
        form = forms.BillingAddressForm(
            shipping_address=self.shipping_address, data=data)
        self.assertTrue(
            form.is_valid(), "Form invalid due to %r" % form.errors)

    def test_selecting_manual_validate_address(self):
        data = {
            'same_as_shipping': 'new',
            'first_name': 'test',
            'last_name': 'test',
            'line1': 'test',
            'line2': 'test',
            'line3': 'test',
            'line4': 'test',
            'postcode': 'test',
            'state': '',
            'country': 'GB'
        }
        form = forms.BillingAddressForm(
            shipping_address=self.shipping_address, data=data)
        self.assertFalse(form.is_valid())
