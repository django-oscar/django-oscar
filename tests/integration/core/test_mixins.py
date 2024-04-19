from django import forms
from django.test import TestCase, override_settings

from oscar.apps.address.forms import AbstractAddressForm
from oscar.apps.address.models import UserAddress
from oscar.apps.order.models import ShippingAddress
from oscar.forms.mixins import PhoneNumberMixin
from oscar.test.factories import CountryFactory


class PhoneNumberMixinTestCase(TestCase):
    def test_mixin_adds_phone_number_field(self):
        class TestForm(PhoneNumberMixin, forms.Form):
            pass

        form = TestForm()
        self.assertIn("phone_number", form.fields)

    def test_mixin_adds_all_phone_number_fields(self):
        class TestForm(PhoneNumberMixin, forms.Form):
            phone_number_fields = {
                "phone_number": {
                    "required": False,
                    "help_text": "",
                    "max_length": 32,
                    "label": "Phone number",
                },
                "another_phone_number": {
                    "required": False,
                    "help_text": "Another phone number help text",
                    "max_length": 32,
                    "label": "Another phone number",
                },
                "one_more_phone_number": {
                    "required": False,
                    "help_text": "",
                    "max_length": 32,
                    "label": "One more phone number",
                },
            }

        form = TestForm()
        self.assertIn("phone_number", form.fields)
        self.assertIn("another_phone_number", form.fields)
        self.assertIn("one_more_phone_number", form.fields)

        field = form.fields["another_phone_number"]
        self.assertEqual(field.help_text, "Another phone number help text")

    def test_mixin_retains_existing_field_properties(self):
        class TestForm(PhoneNumberMixin, forms.ModelForm):
            class Meta:
                model = UserAddress
                fields = ["country", "phone_number"]
                # Override default label and help text
                labels = {"phone_number": "Special number"}
                help_texts = {"phone_number": "Special help text"}

        form = TestForm()
        field = form.fields["phone_number"]
        self.assertEqual(field.label, "Special number")
        self.assertEqual(field.help_text, "Special help text")

    @override_settings(OSCAR_REQUIRED_ADDRESS_FIELDS=("phone_number",))
    def test_required_empty_field_raises_validation_error(self):
        class TestForm(PhoneNumberMixin, AbstractAddressForm):
            phone_number_fields = {
                "phone_number": {
                    "required": True,
                    "help_text": "",
                    "max_length": 32,
                    "label": "Phone number",
                }
            }

            class Meta:
                model = ShippingAddress
                fields = ["country", "phone_number", "postcode"]

        CountryFactory(iso_3166_1_a2="GB", is_shipping_country=True)
        form = TestForm(
            data={"phone_number": "", "country": "GB", "postcode": "WW1 2BB"}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["phone_number"], ["This field is required."])

    @override_settings(OSCAR_REQUIRED_ADDRESS_FIELDS=[])
    def test_optional_empty_field_validates(self):
        class TestForm(PhoneNumberMixin, AbstractAddressForm):
            phone_number_fields = {
                "phone_number": {
                    "required": False,
                    "help_text": "",
                    "max_length": 32,
                    "label": "Phone number",
                }
            }

            class Meta:
                model = ShippingAddress
                fields = ["country", "phone_number", "postcode"]

        CountryFactory(iso_3166_1_a2="GB", is_shipping_country=True)
        form = TestForm(
            data={"phone_number": "", "country": "GB", "postcode": "WW1 2BB"}
        )
        self.assertTrue(form.is_valid())

    @override_settings(OSCAR_REQUIRED_ADDRESS_FIELDS=[])
    def test_invalid_number_fails_validation(self):
        class TestForm(PhoneNumberMixin, AbstractAddressForm):
            phone_number_fields = {
                "phone_number": {
                    "required": False,
                    "help_text": "",
                    "max_length": 32,
                    "label": "Phone number",
                }
            }

            class Meta:
                model = ShippingAddress
                fields = ["country", "phone_number", "postcode"]

        CountryFactory(iso_3166_1_a2="GB", is_shipping_country=True)
        form = TestForm(
            data={"phone_number": "123456", "country": "GB", "postcode": "WW1 2BB"}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["phone_number"],
            ["This is not a valid local phone format for UNITED KINGDOM."],
        )

    @override_settings(OSCAR_REQUIRED_ADDRESS_FIELDS=[])
    def test_valid_number_passes_validation(self):
        class TestForm(PhoneNumberMixin, AbstractAddressForm):
            phone_number_fields = {
                "phone_number": {
                    "required": False,
                    "help_text": "",
                    "max_length": 32,
                    "label": "Phone number",
                }
            }

            class Meta:
                model = ShippingAddress
                fields = ["country", "phone_number", "postcode"]

        CountryFactory(iso_3166_1_a2="GB", is_shipping_country=True)
        form = TestForm(
            data={"phone_number": "02089001234", "country": "GB", "postcode": "WW1 2BB"}
        )
        self.assertTrue(form.is_valid())
