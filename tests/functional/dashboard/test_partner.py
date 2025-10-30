from django.urls import reverse

from oscar.apps.partner import models
from oscar.core.loading import get_class
from oscar.core.compat import get_user_model
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")
User = get_user_model()


class TestPartnerAccessDashboard(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("partner", "view_partner")

    def test_partner_access(self):
        url = reverse("dashboard:partner-list")
        list_page = self.get(url)
        self.assertEqual(list_page.status_code, 200)


class TestPartnerCreateUserDashboard(WebTestCase):
    is_staff = True
    permissions = [
        *DashboardPermission.get("partner", "view_partner"),
        *DashboardPermission.get(User._meta.app_label, "view_user", "add_user"),
    ]

    def test_allows_a_partner_user_to_be_created(self):
        partner = models.Partner.objects.create(name="Acme Ltd")

        url = reverse("dashboard:partner-list")
        list_page = self.get(url)
        detail_page = list_page.click("Manage partner and users")
        user_page = detail_page.click("Link a new user")
        form = user_page.forms["user_partner_form"]
        form["first_name"] = "Maik"
        form["last_name"] = "Hoepfel"
        form["email"] = "maik@gmail.com"
        form["password1"] = "helloworld"
        form["password2"] = "helloworld"
        form.submit()

        self.assertEqual(1, partner.users.all().count())
