from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Permission
from oscar.core.compat import get_user_model
from django.template import Context, Template
from django.apps import apps
from oscar.core.loading import get_class

User = get_user_model()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory


class HasDashboardPermissionTagTests(TestCase):
    """
    Tests for the has_dashboard_permission template tag.
    Covers:
    - Tuple-of-lists (OR-of-ANDs) permission checks
    - Single-list (all permissions required) checks
    - Missing permissions returns False
    - No section in permissions_map returns False
    """

    def setUp(self):
        """
        Create a test user and give them the 'view-order' and 'view-offer' permissions.
        """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="testuser@example.com", username="testuser", password="pass"
        )

        permission_codes = DashboardPermission.get("view-order", "view-offer")
        for perm in permission_codes:
            app_label, codename = perm.split(".", 1)
            permission = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            self.user.user_permissions.add(permission)

    def test_order_list_permissions_tuple_of_lists(self):
        """
        order-list should match tuple-of-lists required permissions.
        """
        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "order-list" "orders_dashboard" as can_view_order %}'
            "{{ can_view_order }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "True")

    def test_offer_list_permissions_single_list(self):
        """
        offer-list should match single list of required permissions.
        """
        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "offer-list" "offers_dashboard" as can_view_offer %}'
            "{{ can_view_offer }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "True")

    def test_returns_false_if_user_missing_permission(self):
        """
        Should return False when user lacks the required permissions.
        """
        self.user.user_permissions.clear()
        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "order-list" "orders_dashboard" as can_view_order %}'
            "{{ can_view_order }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "False")

    def test_returns_false_if_section_not_in_permissions_map(self):
        """
        Should return False if section is not present in the app's permissions_map.
        """
        template = Template(
            "{% load dashboard_permissions %}"
            '{% has_dashboard_permission "nonexistent-section" "orders_dashboard" as can_view %}'
            "{{ can_view }}"
        )
        context = Context({"request": self.factory.get("/"), "user": self.user})
        rendered = template.render(context).strip()
        self.assertEqual(rendered, "False")
