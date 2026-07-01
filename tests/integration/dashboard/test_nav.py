from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from oscar.apps.dashboard.menu import get_nodes
from oscar.apps.dashboard.nav import default_access_fn
from oscar.test.factories import UserFactory


class DashboardAccessFunctionTestCase(TestCase):
    def setUp(self):
        self.staff_user = UserFactory(is_staff=True)
        self.non_staff_user = UserFactory()

    def test_default_access_fn_no_url_name(self):
        self.assertTrue(default_access_fn(self.staff_user, None))

    def test_default_access_fn_staff(self):
        self.assertTrue(default_access_fn(self.staff_user, "dashboard:index"))

    def test_default_access_fn_non_staff_user(self):
        self.assertFalse(default_access_fn(self.non_staff_user, "dashboard:index"))

    def test_default_access_fn_invalid_url_name(self):
        with self.assertRaises(NoReverseMatch):
            default_access_fn(self.staff_user, "invalid_module:index")

    def test_default_access_non_dashboard_url_name(self):
        assert reverse("search:search")
        with self.assertRaises(KeyError):
            default_access_fn(self.staff_user, "search:search")


class DashboardNavTestCase(TestCase):
    def test_staff_user_has_menu(self):
        menu = get_nodes(UserFactory(is_staff=True))
        self.assertTrue(menu)

    def test_non_staff_user_has_empty_menu(self):
        menu = get_nodes(UserFactory())
        self.assertEqual(menu, [])
