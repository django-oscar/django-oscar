from django.urls import reverse

from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class ReportsDashboardTests(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("analytics", "view_userrecord")

    def test_dashboard_is_accessible_to_staff(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)
        self.assertIsOk(response)

    def test_conditional_offers_no_date_range(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "conditional-offers"
        response.forms["generate_report_form"].submit()
        self.assertIsOk(response)

    def test_conditional_offers_with_date_range(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "conditional-offers"
        response.forms["generate_report_form"]["date_from"] = "2017-01-01"
        response.forms["generate_report_form"]["date_to"] = "2017-12-31"
        response.forms["generate_report_form"].submit()
        self.assertIsOk(response)

    def test_conditional_offers_with_date_range_download(self):
        url = reverse("dashboard:reports-index")
        response = self.get(url)

        response.forms["generate_report_form"]["report_type"] = "conditional-offers"
        response.forms["generate_report_form"]["date_from"] = "2017-01-01"
        response.forms["generate_report_form"]["date_to"] = "2017-12-31"
        response.forms["generate_report_form"]["download"] = "true"
        response.forms["generate_report_form"].submit()
        self.assertIsOk(response)
