from django.test import TestCase
from django.contrib.auth import get_user_model

from oscar.core.loading import get_class

User = get_user_model()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class DashboardPermissionCheckTestCase(TestCase):

    def test_get_uses_explicit_permissions_mapping(self):
        """When codename has explicit mapping, .get() returns mapped permissions only."""

        class TestDashboardPermission(DashboardPermission):
            permissions = {"view_product": ["catalogue.view_product_special"]}

        perms = set(TestDashboardPermission.get("catalogue", "view_product"))

        self.assertIn("catalogue.view_product_special", perms)
        self.assertNotIn("catalogue.view_product", perms)

    def test_get_generates_permission_when_no_mapping(self):
        """When no explicit mapping exists, .get() should generate 'app_label.codename'."""
        perms = set(DashboardPermission.get("catalogue", "view_category"))

        self.assertIn("catalogue.view_category", perms)
        self.assertEqual(len(perms), 1)

    def test_get_handles_multiple_codenames(self):
        """Should correctly handle multiple codenames — both mapped and unmapped."""

        class TestDashboardPermission(DashboardPermission):
            permissions = {
                "view_product": ["catalogue.view_product_special"],
                "edit_stock": ["catalogue.change_stockrecord_custom"],
            }

        perms = set(
            TestDashboardPermission.get(
                "catalogue", "view_product", "view_category", "edit_stock"
            )
        )

        # Mapped codenames → use explicit permissions
        self.assertIn("catalogue.view_product_special", perms)
        self.assertIn("catalogue.change_stockrecord_custom", perms)

        # Unmapped codename → auto-generated
        self.assertIn("catalogue.view_category", perms)

        # Original codenames must NOT appear if mapped
        self.assertNotIn("catalogue.view_product", perms)
        self.assertNotIn("catalogue.edit_stock", perms)
        self.assertEqual(len(perms), 3)
