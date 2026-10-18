from django.urls import reverse

from oscar.apps.catalogue.models import Category, Product
from oscar.core.loading import get_class
from oscar.test.factories import CategoryFactory, ProductClassFactory, ProductFactory
from oscar.test.testcases import WebTestCase

DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")

PERMISSION_DENIED_MESSAGE = "You do not have permission to edit this."


class TestProductViewOnlyUser(WebTestCase):
    is_staff = True
    csrf_checks = False
    permissions = DashboardPermission.get("catalogue", "view_product")

    def setUp(self):
        super().setUp()
        self.product = ProductFactory(title="Original title")
        self.url = reverse(
            "dashboard:catalogue-product", kwargs={"pk": self.product.pk}
        )

    def test_update_page_is_read_only(self):
        page = self.get(self.url)

        self.assertTrue(page.context["readonly"])
        self.assertTrue(page.context["title"].startswith("View"))
        self.assertTrue(page.context["form"].fields["title"].disabled)
        self.assertNotContains(page, 'value="save"')

    def test_post_is_blocked(self):
        response = self.post(self.url, params={"title": "Changed title"})

        self.assertRedirects(response, self.url)
        self.assertContains(response.follow(), PERMISSION_DENIED_MESSAGE)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, "Original title")

    def test_delete_is_forbidden(self):
        url = reverse(
            "dashboard:catalogue-product-delete", kwargs={"pk": self.product.pk}
        )

        self.assertNoAccess(self.get(url, status="*"))
        self.assertNoAccess(self.post(url, status="*"))
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_list_hides_delete_action(self):
        page = self.get(reverse("dashboard:catalogue-product-list"))

        self.assertNotContains(
            page,
            reverse(
                "dashboard:catalogue-product-delete", kwargs={"pk": self.product.pk}
            ),
        )


class TestProductChangeUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("catalogue", "view_product", "change_product")

    def test_can_edit_product(self):
        product = ProductFactory(title="Original title")
        url = reverse("dashboard:catalogue-product", kwargs={"pk": product.pk})

        page = self.get(url)
        self.assertFalse(page.context["readonly"])
        form = page.forms["create_update_product_form"]
        form["title"] = "Changed title"
        response = form.submit(name="action", value="save")

        self.assertIsRedirect(response)
        product.refresh_from_db()
        self.assertEqual(product.title, "Changed title")


class TestProductAddOnlyUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("catalogue", "view_product", "add_product")

    def test_can_create_product(self):
        product_class = ProductClassFactory(name="Books", slug="books")
        category = CategoryFactory()
        url = reverse(
            "dashboard:catalogue-product-create",
            kwargs={"product_class_slug": product_class.slug},
        )

        page = self.get(url)
        self.assertFalse(page.context["readonly"])
        form = page.forms["create_update_product_form"]
        form["title"] = "New product"
        form["structure"] = "parent"
        form["productcategory_set-0-category"] = category.id
        response = form.submit(name="action", value="save")

        self.assertIsRedirect(response)
        self.assertTrue(Product.objects.filter(title="New product").exists())


class TestProductDeleteUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get("catalogue", "view_product", "delete_product")

    def test_can_delete_product(self):
        product = ProductFactory()
        url = reverse("dashboard:catalogue-product-delete", kwargs={"pk": product.pk})

        response = self.get(url).forms["delete_product_form"].submit()

        self.assertIsRedirect(response)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())


class TestCategoryViewOnlyUser(WebTestCase):
    is_staff = True
    csrf_checks = False
    permissions = DashboardPermission.get("catalogue", "view_category")

    def setUp(self):
        super().setUp()
        self.category = CategoryFactory(name="Original name")
        self.url = reverse(
            "dashboard:catalogue-category-update", kwargs={"pk": self.category.pk}
        )

    def test_update_page_is_read_only(self):
        page = self.get(self.url)

        self.assertTrue(page.context["readonly"])
        self.assertTrue(page.context["title"].startswith("View"))
        self.assertTrue(page.context["form"].fields["name"].disabled)
        self.assertNotContains(page, 'value="save"')

    def test_post_is_blocked(self):
        response = self.post(self.url, params={"name": "Changed name"})

        self.assertRedirects(response, self.url)
        self.assertContains(response.follow(), PERMISSION_DENIED_MESSAGE)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Original name")

    def test_delete_is_forbidden(self):
        url = reverse(
            "dashboard:catalogue-category-delete", kwargs={"pk": self.category.pk}
        )

        self.assertNoAccess(self.get(url, status="*"))
        self.assertNoAccess(self.post(url, status="*"))
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class TestCategoryChangeUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get(
        "catalogue", "view_category", "change_category"
    )

    def test_can_edit_category(self):
        category = CategoryFactory(name="Original name")
        url = reverse("dashboard:catalogue-category-update", kwargs={"pk": category.pk})

        page = self.get(url)
        self.assertFalse(page.context["readonly"])
        form = page.forms["create_update_category_form"]
        form["name"] = "Changed name"
        response = form.submit(name="action", value="save")

        self.assertIsRedirect(response)
        category.refresh_from_db()
        self.assertEqual(category.name, "Changed name")


class TestCategoryDeleteUser(WebTestCase):
    is_staff = True
    permissions = DashboardPermission.get(
        "catalogue", "view_category", "delete_category"
    )

    def test_can_delete_category(self):
        category = CategoryFactory()
        url = reverse("dashboard:catalogue-category-delete", kwargs={"pk": category.pk})

        response = self.get(url).forms["delete_category_form"].submit()

        self.assertIsRedirect(response)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
