from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.apps.address import models
from oscar.apps.order.models import ShippingAddress

User = get_user_model()


class TestUserAddress(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")
        self.country = models.Country(
            iso_3166_1_a2='GB', name="UNITED KINGDOM")

    def test_converts_postcode_to_uppercase_when_saving(self):
        address = models.UserAddress.objects.create(
            last_name='Barrington',
            line1="75 Smith Road",
            postcode="n4 8ty",
            country=self.country, user=self.user)
        self.assertEquals("N4 8TY", address.postcode)

    def test_strips_whitespace_when_saving(self):
        a = models.UserAddress.objects.create(
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country, user=self.user)
        self.assertEquals("N4 8TY", a.postcode)
        self.assertEquals("75 Smith Road", a.line1)

    def test_active_address_fields_skips_whitespace_only_fields(self):
        a = models.UserAddress(
            first_name="   ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        active_fields = a.active_address_fields()
        self.assertEquals("Barrington", active_fields[0])

    def test_hashing_with_utf8(self):
        a = models.UserAddress(
            first_name=u"\u0141ukasz Smith",
            last_name=u'Smith',
            line1=u"75 Smith Road",
            postcode=u"n4 8ty",
            country=self.country)
        a.active_address_fields()

    def test_ignores_whitespace_when_hashing(self):
        a1 = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a2 = models.UserAddress(
            first_name=" Terry",
            last_name='   Barrington',
            line1="  75 Smith Road  ",
            postcode="N4 8ty",
            country=self.country)
        self.assertEquals(a1.generate_hash(), a2.generate_hash())

    def test_populate_shipping_address_doesnt_set_id(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertIsNone(sa.id)

    def test_populated_shipping_address_has_same_summary_user_address(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertEquals(sa.summary, a.summary)

    def test_summary_is_property(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        self.assertEquals(
            u"Terry Barrington, 75 Smith Road, N4 8TY, UNITED KINGDOM",
            a.summary)
