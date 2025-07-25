from decimal import Decimal as D

from django.urls import reverse

from oscar.apps.shipping import models
from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class TestShippingMethodDashboard(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("shipping_method")

    def test_for_smoke(self):
        list_page = self.get(reverse("dashboard:shipping-method-list"))

        # Create a shipping method
        create_page = list_page.click(linkid="create_new_shipping_method")
        create_page.forms["create_update_weight_based_form"]["name"] = "My method"
        detail_page = (
            create_page.forms["create_update_weight_based_form"].submit().follow()
        )
        self.assertInContext(detail_page, "method")
        self.assertEqual(1, models.WeightBased.objects.all().count())
        method = models.WeightBased.objects.all()[0]

        # Edit shipping method
        edit_page = detail_page.click(linkid="edit_method")
        edit_page.forms["create_update_weight_based_form"]["name"] = "My new method"
        reloaded_detail_page = (
            edit_page.forms["create_update_weight_based_form"].submit().follow()
        )
        reloaded_method = models.WeightBased.objects.get(id=method.id)
        self.assertEqual("My new method", reloaded_method.name)

        # Add a weight band
        reloaded_detail_page.forms["add_new_weight_band_form"]["upper_limit"] = "0.1"
        reloaded_detail_page.forms["add_new_weight_band_form"]["charge"] = "2.99"
        reloaded_detail_page = (
            reloaded_detail_page.forms["add_new_weight_band_form"].submit().follow()
        )
        self.assertEqual(1, method.bands.all().count())
        band = method.bands.all()[0]

        # Edit weight band
        edit_band_page = reloaded_detail_page.click(linkid="edit_band_%s" % band.id)
        edit_band_page.forms["create_update_weight_band_form"]["charge"] = "3.99"
        reloaded_detail_page = (
            edit_band_page.forms["create_update_weight_band_form"].submit().follow()
        )
        reloaded_band = method.bands.get(id=band.id)
        self.assertEqual(D("3.99"), reloaded_band.charge)

        # Delete weight band
        delete_band_page = reloaded_detail_page.click(
            linkid="delete_band_%s" % reloaded_band.id
        )
        reloaded_detail_page = (
            delete_band_page.forms["delete_weight_band_form"].submit().follow()
        )
        self.assertEqual(0, method.bands.all().count())

        # Delete shipping method
        delete_page = reloaded_detail_page.click(linkid="delete_method")
        delete_page.forms["delete_weight_based_form"].submit().follow()
        self.assertEqual(0, models.WeightBased.objects.all().count())
