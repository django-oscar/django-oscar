from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.test.factories import create_product

User = get_user_model()


class AuthTokenTest(TestCase):
    def test_token_is_obtained_with_email(self):
        User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        response = self.client.post(
            reverse("api-auth-token"),
            {"username": "jdoe@example.com", "password": "s3cret-pass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["token"])

    def test_wrong_password_is_rejected(self):
        User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        response = self.client.post(
            reverse("api-auth-token"),
            {"username": "jdoe@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())

    def test_registration_is_enabled(self):
        response = self.client.post(
            reverse("api-register"),
            {
                "email": "new@example.com",
                "password1": "Sup3r-secret-42",
                "password2": "Sup3r-secret-42",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())


class MobileCatalogueTest(TestCase):
    def setUp(self):
        self.shirts = create_from_breadcrumbs("Clothing > Shirts")
        self.clothing = self.shirts.get_parent()
        self.books = create_from_breadcrumbs("Books")
        self.shirt = create_product(title="Shirt", price=12, num_in_stock=3)
        self.shirt.categories.add(self.shirts)
        self.book = create_product(title="Book", price=5, num_in_stock=1)
        self.book.categories.add(self.books)

    def test_product_list_inlines_price_and_availability(self):
        data = self.client.get(reverse("product-list")).json()
        self.assertEqual(len(data), 2)
        shirt = next(p for p in data if p["id"] == self.shirt.pk)
        self.assertEqual(shirt["price"]["excl_tax"], "12.00")
        self.assertTrue(shirt["availability"]["is_available_to_buy"])
        self.assertEqual(shirt["categories"], [{"id": self.shirts.pk, "name": "Shirts"}])

    def test_product_list_filters_by_category_and_descendants(self):
        url = reverse("product-list")
        ids = [p["id"] for p in self.client.get(url, {"category": self.clothing.pk}).json()]
        self.assertEqual(ids, [self.shirt.pk])
        self.assertEqual(self.client.get(url, {"category": 999}).json(), [])

    def test_product_detail_inlines_price(self):
        data = self.client.get(reverse("product-detail", args=[self.book.pk])).json()
        self.assertEqual(data["title"], "Book")
        self.assertEqual(data["price"]["excl_tax"], "5.00")

    def test_category_list_by_parent(self):
        url = reverse("category-list")
        roots = {c["name"]: c for c in self.client.get(url).json()}
        self.assertEqual(set(roots), {"Clothing", "Books"})
        self.assertTrue(roots["Clothing"]["has_children"])
        self.assertIsNone(roots["Clothing"]["parent_id"])

        children = self.client.get(url, {"parent": self.clothing.pk}).json()
        self.assertEqual([c["name"] for c in children], ["Shirts"])
        self.assertEqual(children[0]["parent_id"], self.clothing.pk)
        self.assertFalse(children[0]["has_children"])
