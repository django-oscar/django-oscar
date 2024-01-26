from http import client as http_client

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext
from django.core.management import call_command

from oscar.apps.catalogue.models import Category
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase


class TestProductDetailView(WebTestCase):
    def test_enforces_canonical_url(self):
        p = create_product()
        kwargs = {"product_slug": "1_wrong-but-valid-slug_1", "pk": p.id}
        wrong_url = reverse("catalogue:detail", kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(p.get_absolute_url() in response.location)

    def test_child_to_parent_redirect(self):
        """
        We test against separate view in order to isolate tested product
        detail view, since default value of `ProductDetailView.enforce_parent`
        property has changed. Thus, by default the view should not redirect
        to the parent page, but we need to make sure that original solution
        works well.
        """
        parent_product = create_product(structure="parent")
        kwargs = {"product_slug": parent_product.slug, "pk": parent_product.id}
        parent_product_url = reverse("catalogue:parent_detail", kwargs=kwargs)

        child = create_product(
            title="Variant 1", structure="child", parent=parent_product
        )
        kwargs = {"product_slug": child.slug, "pk": child.id}
        child_url = reverse("catalogue:parent_detail", kwargs=kwargs)

        response = self.app.get(parent_product_url)
        self.assertEqual(http_client.OK, response.status_code, response.location)

        response = self.app.get(child_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)

    def test_is_public_on(self):
        product = create_product(upc="kleine-bats", is_public=True)

        kwargs = {"product_slug": product.slug, "pk": product.id}
        url = reverse("catalogue:detail", kwargs=kwargs)
        response = self.app.get(url)

        self.assertEqual(response.status_code, http_client.OK)

    def test_is_public_off(self):
        product = create_product(upc="kleine-bats", is_public=False)

        kwargs = {"product_slug": product.slug, "pk": product.id}
        url = reverse("catalogue:detail", kwargs=kwargs)
        response = self.app.get(url, expect_errors=True)

        self.assertEqual(response.status_code, http_client.NOT_FOUND)

    def test_does_not_go_into_redirect_loop(self):
        "when a product slug contains a colon, there should be no redirect loop"
        with self.settings(ROOT_URLCONF="tests._site.specialurls"):
            product = create_product(slug="no-redirect", is_public=True)
            kwargs = {"product_slug": "si-redirect", "pk": product.id}
            url = reverse("catalogue:detail", kwargs=kwargs)
            response = self.app.get(url, expect_errors=True)
            self.assertIsRedirect(response)
            response = self.app.get(response["Location"])
            self.assertIsNotRedirect(response)


class TestProductListView(WebTestCase):
    def setUp(self):
        call_command("rebuild_index", "--noinput")

    def test_shows_add_to_basket_button_for_available_product(self):
        product = create_product(num_in_stock=1)
        page = self.app.get(reverse("catalogue:index"))
        self.assertContains(page, product.title)
        self.assertContains(page, gettext("Add to basket"))

    def test_shows_not_available_for_out_of_stock_product(self):
        product = create_product(num_in_stock=0)

        page = self.app.get(reverse("catalogue:index"))

        self.assertContains(page, product.title)
        self.assertContains(page, "Unavailable")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = settings.OSCAR_PRODUCTS_PER_PAGE
        title = "Product #%d"
        for idx in range(0, int(1.5 * per_page)):
            create_product(title=title % idx)

        page = self.app.get(reverse("catalogue:index"))

        self.assertContains(page, "Page 1 of 2")

    def test_is_public_on(self):
        product = create_product(upc="grote-bats", is_public=True)
        page = self.app.get(reverse("catalogue:index"))
        products_on_page = list(page.context["products"])
        products_on_page = [prd.object for prd in products_on_page]
        self.assertEqual(products_on_page, [product])

    def test_is_public_off(self):
        create_product(upc="kleine-bats", is_public=False)
        page = self.app.get(reverse("catalogue:index"))
        products_on_page = list(page.context["products"])
        self.assertEqual(products_on_page, [])

    def test_invalid_page_redirects_to_index(self):
        create_product()
        products_list_url = reverse("catalogue:index")
        response = self.app.get("%s?page=200" % products_list_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirectsTo(response, "catalogue:index")


class TestProductCategoryView(WebTestCase):
    def setUp(self):
        self.category = Category.add_root(name="Products")

    def test_browsing_works(self):
        correct_url = self.category.get_absolute_url()
        response = self.app.get(correct_url)
        self.assertEqual(http_client.OK, response.status_code)

    def test_enforces_canonical_url(self):
        kwargs = {"category_slug": "1_wrong-but-valid-slug_1", "pk": self.category.pk}
        wrong_url = reverse("catalogue:category", kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(self.category.get_absolute_url() in response.location)

    def test_is_public_off(self):
        category = Category.add_root(name="Foobars", is_public=False)
        response = self.app.get(category.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
        return category

    def test_is_public_on(self):
        category = Category.add_root(name="Barfoos", is_public=True)
        response = self.app.get(category.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)
        return category

    def test_browsable_contains_public_child(self):
        "If the parent is public the child should be in browsable if it is public as well"
        cat = self.test_is_public_on()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child in Category.objects.all().browsable())

        child.is_public = False
        child.save()
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_browsable_hides_public_child(self):
        "If the parent is not public the child should not be in browsable evn if it is public"
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_is_public_child(self):
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        response = self.app.get(child.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)

        child.is_public = False
        child.save()
        response = self.app.get(child.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
