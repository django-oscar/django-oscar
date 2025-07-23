from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Permission
from oscar.core.compat import get_user_model
from django.template import Context, Template
from oscar.core.loading import get_class

User = get_user_model()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class HasDashboardPermissionTagTests(TestCase):
    """
    Tests for the has_dashboard_permission template tag.
    """

    def setUp(self):
        """
        Set up a user with specific permissions for testing.
        """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="testuser@example.com", username="testuser", password="pass"
        )
        self.section = "order"

        for perm_codename in DashboardPermission.permissions.get(self.section, []):
            if perm_codename == "is_staff":
                continue
            app_label, codename = perm_codename.split(".")
            permission = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
            self.user.user_permissions.add(permission)

    def test_has_dashboard_permission_returns_true(self):
        """
        Test that the has_dashboard_permission template tag returns True for a user with permission.
        """
        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "order" as can_view_order %}'
            "{{ can_view_order }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        context["request"].user = self.user
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "True")

    def test_has_dashboard_permission_returns_false_if_missing_perm(self):
        """
        Test that the has_dashboard_permission template tag returns False for a user without permission.
        """
        self.user.user_permissions.clear()

        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "order" as can_view_order %}'
            "{{ can_view_order }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        context["request"].user = self.user
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "False")
