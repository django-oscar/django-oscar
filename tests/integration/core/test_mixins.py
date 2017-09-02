from django import forms
from django.test import TestCase

from oscar.apps.address.models import UserAddress
from oscar.views.generic import PhoneNumberMixin


class PhoneNumberMixinTestCase(TestCase):

    def test_mixin_adds_phone_number_field(self):

        class TestForm(PhoneNumberMixin, forms.Form):
            pass

        form = TestForm()
        self.assertIn('phone_number', form.fields)

    def test_mixin_retains_existing_field_properties(self):

        class TestForm(PhoneNumberMixin, forms.ModelForm):

            class Meta:
                model = UserAddress
                fields = ['country', 'phone_number']
                # Override default label and help text
                labels = {"phone_number": "Special number"}
                help_texts = {"phone_number": "Special help text"}

        form = TestForm()
        field = form.fields['phone_number']
        self.assertEqual(field.label, "Special number")
        self.assertEqual(field.help_text, "Special help text")
