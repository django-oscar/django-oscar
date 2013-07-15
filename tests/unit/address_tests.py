# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core import exceptions

from nose.tools import raises

from oscar.core.compat import get_user_model
from oscar.apps.address.models import UserAddress, Country


User = get_user_model()


class UserAddressTest(TestCase):

    def test_titleless_salutation_is_stripped(self):
        a = UserAddress(
            last_name='Barrington', line1="75 Smith Road", postcode="N4 8TY")
        self.assertEquals("Barrington", a.salutation)

    def test_city_is_alias_of_line4(self):
        a = UserAddress(
            last_name='Barrington',
            line1="75 Smith Road",
            line4="London",
            postcode="n4 8ty")
        self.assertEqual('London', a.city)


VALID_POSTCODES = [
    ('GB', 'N1 9RT'),
    ('SK', '991 41'),
    ('CZ', '612 00'),
    ('CC', '6799'),
    ('CY', '8240'),
    ('MC', '98000'),
    ('SH', 'STHL 1ZZ'),
    ('JP', '150-2345'),
    ('PG', '314'),
    ('HN', '41202'),
    # It works for small cases as well
    ('GB', 'sw2 1rw'),
]


INVALID_POSTCODES = [
    ('GB', 'not-a-postcode'),
    ('DE', '123b4'),
]


def assert_valid_postcode(country_value, postcode_value):
    country = Country(iso_3166_1_a2=country_value)
    address = UserAddress(country=country, postcode=postcode_value)
    address.clean()


@raises(exceptions.ValidationError)
def assert_invalid_postcode(country_value, postcode_value):
    country = Country(iso_3166_1_a2=country_value)
    address = UserAddress(country=country, postcode=postcode_value)
    address.clean()


def test_postcode_is_validated_for_country():
    for country, postcode in VALID_POSTCODES:
        yield assert_valid_postcode, country, postcode


def test_postcode_is_only_valid():
    for country, postcode in INVALID_POSTCODES:
        yield assert_invalid_postcode, country, postcode
