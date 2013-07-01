# -*- coding: utf-8 -*-
from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.apps.address.models import UserAddress


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
