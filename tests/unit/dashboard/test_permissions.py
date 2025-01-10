from django.test import TestCase
from django.contrib.auth import get_user_model

from oscar.core.loading import get_class
from oscar.test.factories import UserFactory
from oscar.test.testcases import add_permissions

User = get_user_model()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class DashboardPermissionCheckTestCase(TestCase):
    def test_user_has_dashboard_permissions(self):
        user = UserFactory()
        self.client.force_login(user)
        self.assertFalse(DashboardPermission.has_dashboard_perms(user))

        # reloading user to purge the _perm_cache
        user = User._default_manager.get(pk=user.pk)
        add_permissions(user, DashboardPermission.permissions["product"])
        self.assertTrue(DashboardPermission.has_dashboard_perms(user))
