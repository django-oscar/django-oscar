#-*- coding: utf-8 -*-
from django.test.testcases import TestCase
from django.db import models
from django import forms

from oscar.core.phonenumber import PhoneNumber
from oscar.models.fields import PhoneNumberField


class MandatoryPhoneNumber(models.Model):
    phone_number = PhoneNumberField()

    class Meta:
        app_label = 'tests'


class OptionalPhoneNumber(models.Model):
    phone_number = PhoneNumberField(blank=True, default='')

    class Meta:
        app_label = 'tests'


class PhoneNumberForm(forms.ModelForm):

    class Meta:
        model = MandatoryPhoneNumber
        fields = ['phone_number']


valid_number = '+4917696842671'
equal_number_strings = ['+44 113 8921113', '+441138921113']
local_numbers = [
    ('GB', '01606 751 78'),
    ('DE', '0176/96842671'),
    ]
invalid_numbers = ['+44 113 892111', ]


class TestPhoneNumberTestCase(TestCase):

    def test_valid_numbers_are_valid(self):
        numbers = [PhoneNumber.from_string(number_string)
                   for number_string in equal_number_strings + [valid_number]]
        self.assertTrue(all([number.is_valid() for number in numbers]))
        numbers = [PhoneNumber.from_string(number_string, region=region)
                   for region, number_string in local_numbers]
        self.assertTrue(all([number.is_valid() for number in numbers]))

    def test_invalid_numbers_are_invalid(self):
        numbers = [PhoneNumber.from_string(number_string)
                   for number_string in invalid_numbers]
        self.assertTrue(all([not number.is_valid() for number in numbers]))


class TestPhoneNumberFieldTestCase(TestCase):

    def test_objects_with_same_number_are_equal(self):
        numbers = [
            MandatoryPhoneNumber(phone_number=number_string).phone_number
            for number_string in equal_number_strings]
        self.assertTrue(all(n == numbers[0] for n in numbers))

    def test_field_returns_correct_type(self):
        instance = OptionalPhoneNumber()
        self.assertEqual(instance.phone_number, None)
        instance.phone_number = valid_number
        self.assertEqual(type(instance.phone_number), PhoneNumber)

    def test_can_assign_string_phone_number(self):
        instance = MandatoryPhoneNumber()
        instance.phone_number = valid_number
        self.assertEqual(type(instance.phone_number), PhoneNumber)
        self.assertEqual(instance.phone_number.as_e164, valid_number)

    def test_can_assign_phone_number(self):
        phone = MandatoryPhoneNumber()
        phone.phone_number = PhoneNumber.from_string(valid_number)
        self.assertEqual(type(phone.phone_number), PhoneNumber)
        self.assertEqual(phone.phone_number.as_e164, valid_number)


class TestPhoneNumberFormFieldTestCase(TestCase):

    def test_form_to_instance_flow(self):
        form = PhoneNumberForm({'phone_number': valid_number})
        self.assertTrue(form.is_valid())
        instance = form.save(commit=False)
        self.assertTrue(type(instance.phone_number), PhoneNumber)
        self.assertEqual(instance.phone_number.as_e164, valid_number)
