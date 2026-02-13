from django.urls import reverse

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.catalogue.models import Category
from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase

from treebeard import __version__ as treebeard_version

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class TestCategoryDashboard(WebTestCase):
    is_staff = True
    csrf_checks = False
    permissions = DashboardPermission.get(
        "catalogue",
        "view_product",
        "view_category",
        "delete_category",
        "add_category",
    )
    TREEBEARD_POS_FIELD = (
        "treebeard_position" if treebeard_version >= "5" else "_position"
    )
    TREEBEARD_REF_FIELD = (
        "treebeard_ref_node" if treebeard_version >= "5" else "_ref_node_id"
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
        form[self.TREEBEARD_POS_FIELD] = "right"
        form[self.TREEBEARD_REF_FIELD] = a.id
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
        form[self.TREEBEARD_POS_FIELD] = "left"
        form[self.TREEBEARD_REF_FIELD] = c.id
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

    def test_make_public(self):
        Category.objects.update(is_public=False)
        a = Category.objects.get(name="A")
        params = {"action": "make_public", "selected_category": [a.id]}
        response = self.post(
            reverse("dashboard:catalogue-category-list"), params=params
        )
        self.assertIsRedirect(response)
        a.refresh_from_db()
        self.assertTrue(a.is_public)

    def test_make_non_public(self):
        b = Category.objects.get(name="B")
        params = {"action": "make_non_public", "selected_category": [b.id]}
        response = self.post(
            reverse("dashboard:catalogue-category-detail-list", args=(b.pk,)),
            params=params,
        )
        self.assertIsRedirect(response)
        b.refresh_from_db()
        self.assertFalse(b.is_public)
