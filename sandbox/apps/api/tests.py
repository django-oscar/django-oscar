from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.test.basket import add_product
from oscar.test.factories import (
    BasketFactory,
    UserAddressFactory,
    create_order,
    create_product,
)
from rest_framework.authtoken.models import Token

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
        data = self.client.get(reverse("product-list")).json()["results"]
        self.assertEqual(len(data), 2)
        shirt = next(p for p in data if p["id"] == self.shirt.pk)
        self.assertEqual(shirt["price"]["excl_tax"], "12.00")
        self.assertTrue(shirt["availability"]["is_available_to_buy"])
        self.assertEqual(shirt["categories"], [{"id": self.shirts.pk, "name": "Shirts"}])

    def test_product_list_filters_by_category_and_descendants(self):
        url = reverse("product-list")
        response = self.client.get(url, {"category": self.clothing.pk}).json()
        self.assertEqual([p["id"] for p in response["results"]], [self.shirt.pk])
        self.assertEqual(self.client.get(url, {"category": 999}).json()["results"], [])

    def test_product_list_is_paginated_newest_first(self):
        url = reverse("product-list")
        first = self.client.get(url, {"page_size": 1}).json()
        self.assertEqual(first["count"], 2)
        self.assertEqual([p["id"] for p in first["results"]], [self.book.pk])
        self.assertIsNotNone(first["next"])

        second = self.client.get(url, {"page_size": 1, "page": 2}).json()
        self.assertEqual([p["id"] for p in second["results"]], [self.shirt.pk])
        self.assertIsNone(second["next"])

        self.assertEqual(self.client.get(url, {"page": 3}).status_code, 404)

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


class UserDetailsTest(TestCase):
    """The app profile screen reads the signed-in user, orders and addresses"""

    def setUp(self):
        self.user = User.objects.create_user(
            "jdoe", "jdoe@example.com", "s3cret-pass", first_name="Jane", last_name="Doe"
        )
        token = Token.objects.create(user=self.user)
        self.auth = {"HTTP_AUTHORIZATION": f"Token {token.key}"}

    def test_login_get_returns_the_user(self):
        response = self.client.get(reverse("api-login"), **self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.user.pk,
                "email": "jdoe@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "date_joined": response.json()["date_joined"],
            },
        )

    def test_login_get_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("api-login")).status_code, 405)

    def test_orders_and_addresses_are_lists_of_the_user(self):
        other = User.objects.create_user("other", "other@example.com", "s3cret-pass")
        create_order(user=self.user)
        create_order(user=other)
        UserAddressFactory(user=self.user)
        UserAddressFactory(user=other, line1="2 Other Road")

        orders = self.client.get(reverse("order-list"), **self.auth).json()
        addresses = self.client.get(reverse("useraddress-list"), **self.auth).json()

        self.assertEqual([o["email"] for o in orders], ["jdoe@example.com"])
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]["line1"], "1 King Road")

    def test_order_history_has_ids_and_line_titles(self):
        basket = BasketFactory()
        add_product(basket, Decimal("12.00"), 2, create_product(title="Linen Shirt"))
        order = create_order(user=self.user, basket=basket)
        other_order = create_order(
            user=User.objects.create_user("other", "other@example.com", "s3cret-pass")
        )

        orders = self.client.get(reverse("order-list"), **self.auth).json()
        lines = self.client.get(
            reverse("order-lines-list", args=[order.pk]), **self.auth
        ).json()
        other_lines = self.client.get(
            reverse("order-lines-list", args=[other_order.pk]), **self.auth
        ).json()

        self.assertEqual([o["id"] for o in orders], [order.pk])
        self.assertEqual(
            [(line["title"], line["quantity"]) for line in lines], [("Linen Shirt", 2)]
        )
        self.assertEqual(other_lines, [])
