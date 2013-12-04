#-*- coding: utf-8 -*-
from django.test.testcases import TestCase
from django.db import models

from oscar.core.phonenumber import PhoneNumber
from oscar.models.fields import PhoneNumberField


class MandatoryPhoneNumber(models.Model):
    phone_number = PhoneNumberField()


class OptionalPhoneNumber(models.Model):
    phone_number = PhoneNumberField(blank=True, default='')


test_number_1 = '+414204242'
equal_number_strings = ['+44 113 8921113', '+441138921113']
local_numbers = [
    ('GB', '01606 751 78'),
    ('DE', '0176/96842671'),
    ]
invalid_numbers = ['+44 113 892111', ]


class TestPhoneNumberTestCase(TestCase):

    def test_valid_numbers_are_valid(self):
        numbers = [PhoneNumber.from_string(number_string)
                   for number_string in equal_number_strings]
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
        self.assertTrue(all(n==numbers[0] for n in numbers))

    def test_field_returns_correct_type(self):
        model = OptionalPhoneNumber()
        self.assertEqual(model.phone_number, None)
        model.phone_number = '+49 176 96842671'
        self.assertEqual(type(model.phone_number), PhoneNumber)

    def test_can_assign_string_phone_number(self):
        opt_phone = OptionalPhoneNumber()
        opt_phone.phone_number = test_number_1
        self.assertEqual(type(opt_phone.phone_number), PhoneNumber)
        self.assertEqual(opt_phone.phone_number.as_e164, test_number_1)
