from django.urls import reverse

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.catalogue.models import Category
from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class TestCategoryDashboard(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get(
        "catalogue",
        "view_product",
        "view_category",
        "delete_category",
        "add_category",
    )

    def setUp(self):
        super().setUp()
        self.staff = self.user
        create_from_breadcrumbs("A > B > C")

    def test_redirects_to_main_dashboard_after_creating_top_level_category(self):
        a = Category.objects.get(name="A")
        category_add = self.app.get(
            reverse("dashboard:catalogue-category-create"), user=self.staff
        )
        form = category_add.forms["create_update_category_form"]
        form["name"] = "Top-level category"
        form["_position"] = "right"
        form["_ref_node_id"] = a.id
        response = form.submit()
        self.assertRedirects(response, reverse("dashboard:catalogue-category-list"))

    def test_redirects_to_parent_list_after_creating_child_category(self):
        b = Category.objects.get(name="B")
        c = Category.objects.get(name="C")
        category_add = self.app.get(
            reverse("dashboard:catalogue-category-create"), user=self.staff
        )
        form = category_add.forms["create_update_category_form"]
        form["name"] = "Child category"
        form["_position"] = "left"
        form["_ref_node_id"] = c.id
        response = form.submit()
        self.assertRedirects(
            response, reverse("dashboard:catalogue-category-detail-list", args=(b.pk,))
        )

    def test_handles_invalid_form_gracefully(self):
        dashboard_index = self.app.get(reverse("dashboard:index"), user=self.staff)
        category_index = dashboard_index.click("Categories")
        category_add = category_index.click("Create new category")
        response = category_add.forms["create_update_category_form"].submit()
        self.assertEqual(200, response.status_code)

    def test_name_filter(self):
        page = self.get("%s?name=B" % reverse("dashboard:catalogue-category-list"))
        category = Category.objects.get(name="B")
        self.assertIn(category, page.context["category_list"])
