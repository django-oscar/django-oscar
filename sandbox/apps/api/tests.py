from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.core.loading import get_model
from oscar.test.basket import add_product
from oscar.test.factories import (
    BasketFactory,
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    RangeFactory,
    VoucherFactory,
    CountryFactory,
    UserAddressFactory,
    create_order,
    create_product,
)
from rest_framework.authtoken.models import Token

User = get_user_model()
ProductReview = get_model("reviews", "ProductReview")


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

    def search(self, q, **params):
        response = self.client.get(reverse("product-list"), {"q": q, **params})
        return [p["id"] for p in response.json()["results"]]

    def test_product_list_searches_title_description_and_upc(self):
        self.book.description = "A novel about the sea"
        self.book.upc = "978-SEA"
        self.book.save()
        self.assertEqual(self.search("shi"), [self.shirt.pk])
        self.assertEqual(self.search("NOVEL"), [self.book.pk])
        self.assertEqual(self.search("978-sea"), [self.book.pk])
        self.assertEqual(self.search("978"), [])  # the UPC must match whole

    def test_product_search_needs_every_word(self):
        self.book.description = "A novel about the sea"
        self.book.save()
        self.assertEqual(self.search("book sea"), [self.book.pk])
        self.assertEqual(self.search("book shirt"), [])

    def test_product_search_within_a_category(self):
        self.assertEqual(self.search("shirt", category=self.clothing.pk), [self.shirt.pk])
        self.assertEqual(self.search("book", category=self.clothing.pk), [])

    def test_blank_search_lists_everything(self):
        self.assertEqual(self.search("   "), [self.book.pk, self.shirt.pk])

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


class ProductReviewApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "jdoe", "jdoe@example.com", "s3cret-pass", first_name="Jane", last_name="Doe"
        )
        self.auth = {
            "HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"
        }
        self.product = create_product(title="Linen Shirt", price=12, num_in_stock=3)
        self.url = reverse("api-product-reviews", args=[self.product.pk])

    def review(self, **data):
        payload = {"score": 4, "title": "Nice", "body": "Fits well."}
        payload.update(data)
        return self.client.post(
            self.url, payload, content_type="application/json", **self.auth
        )

    @override_settings(OSCAR_MODERATE_REVIEWS=False)
    def test_review_is_listed_and_counted_on_the_product(self):
        response = self.review()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "approved")

        reviews = self.client.get(self.url).json()
        self.assertEqual(
            [(r["score"], r["title"], r["reviewer"]) for r in reviews],
            [(4, "Nice", "Jane Doe")],
        )
        self.assertNotIn("email", reviews[0])

        product = self.client.get(
            reverse("product-detail", args=[self.product.pk])
        ).json()
        self.assertEqual(product["reviews_count"], 1)
        self.assertEqual(product["rating"], 4.0)
        listed = self.client.get(reverse("product-list")).json()["results"]
        self.assertEqual(listed[0]["reviews_count"], 1)

    def test_one_review_per_product(self):
        self.review()
        response = self.review(title="Again")
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())

    def test_writing_a_review_requires_authentication(self):
        response = self.client.post(
            self.url,
            {"score": 4, "title": "Nice", "body": "Fits well."},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_score_must_be_between_1_and_5(self):
        self.assertEqual(self.review(score=0).status_code, 400)
        self.assertEqual(self.review(score=6).status_code, 400)

    @override_settings(OSCAR_MODERATE_REVIEWS=True)
    def test_moderated_reviews_are_only_listed_for_their_author(self):
        review_id = self.review().json()["id"]

        self.assertEqual(self.client.get(self.url).json(), [])
        mine = self.client.get(reverse("api-my-reviews"), **self.auth).json()
        self.assertEqual(
            [(r["product"], r["product_title"], r["status"]) for r in mine],
            [(self.product.pk, "Linen Shirt", "pending")],
        )

        # approved in the dashboard: published and counted
        review = ProductReview.objects.get(pk=review_id)
        review.status = ProductReview.APPROVED
        review.save()
        self.assertEqual([r["id"] for r in self.client.get(self.url).json()], [review_id])
        product = self.client.get(reverse("product-detail", args=[self.product.pk])).json()
        self.assertEqual(product["reviews_count"], 1)

    def test_my_reviews_require_authentication(self):
        self.assertEqual(self.client.get(reverse("api-my-reviews")).status_code, 401)


class UserAddressApiTest(TestCase):
    """Address book edited from the app (oscarapi /api/useraddresses/)"""

    def setUp(self):
        CountryFactory(iso_3166_1_a2="FR", printable_name="France")
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.auth = {
            "HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"
        }
        self.address = {
            "first_name": "Jane",
            "last_name": "Doe",
            "line1": "1 rue de la Paix",
            "line4": "Paris",
            "postcode": "75002",
            "country": "http://testserver" + reverse("country-detail", args=["FR"]),
            "is_default_for_shipping": True,
        }

    def post(self, data):
        return self.client.post(
            reverse("useraddress-list"), data, content_type="application/json", **self.auth
        )

    def test_create_update_and_delete_an_address(self):
        created = self.post(self.address)
        self.assertEqual(created.status_code, 201)
        url = reverse("useraddress-detail", args=[created.json()["id"]])

        updated = self.client.put(
            url, {**self.address, "line2": "Bat B"}, content_type="application/json", **self.auth
        )
        self.assertEqual(updated.json()["line2"], "Bat B")

        self.assertEqual(self.client.delete(url, **self.auth).status_code, 204)
        self.assertEqual(self.client.get(reverse("useraddress-list"), **self.auth).json(), [])

    def test_only_one_default_shipping_address(self):
        first = self.post(self.address).json()["id"]
        self.post({**self.address, "line1": "2 rue Royale"})

        addresses = self.client.get(reverse("useraddress-list"), **self.auth).json()
        defaults = {a["id"]: a["is_default_for_shipping"] for a in addresses}
        self.assertFalse(defaults[first])
        self.assertEqual(sum(defaults.values()), 1)

    def test_same_address_twice_is_refused_with_406(self):
        self.post(self.address)
        self.assertEqual(self.post(self.address).status_code, 406)

    def test_addresses_of_other_users_are_hidden(self):
        address_id = self.post(self.address).json()["id"]
        other = User.objects.create_user("other", "other@example.com", "s3cret-pass")
        other_auth = {"HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=other).key}"}

        response = self.client.delete(
            reverse("useraddress-detail", args=[address_id]), **other_auth
        )
        self.assertEqual(response.status_code, 404)


class AccountApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.token = Token.objects.create(user=self.user).key
        self.auth = {"HTTP_AUTHORIZATION": f"Token {self.token}"}

    def test_name_can_be_changed_but_not_the_email(self):
        response = self.client.patch(
            reverse("api-account"),
            {"first_name": "Jane", "last_name": "Doe", "email": "other@example.com"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "Jane")
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "Jane Doe")
        self.assertEqual(self.user.email, "jdoe@example.com")

    def change_password(self, old, new, repeat=None):
        return self.client.post(
            reverse("api-account-password"),
            {"old_password": old, "new_password1": new, "new_password2": repeat or new},
            content_type="application/json",
            **self.auth,
        )

    def test_password_change_keeps_the_token(self):
        self.assertEqual(self.change_password("s3cret-pass", "N3w-pass-word").status_code, 204)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("N3w-pass-word"))
        self.assertEqual(self.client.get(reverse("api-account"), **self.auth).status_code, 200)

    def test_password_change_errors(self):
        self.assertIn("old_password", self.change_password("wrong", "N3w-pass-word").json())
        self.assertIn("new_password2", self.change_password("s3cret-pass", "short").json())
        self.assertIn(
            "new_password2", self.change_password("s3cret-pass", "N3w-pass-word", "other").json()
        )

    def test_account_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("api-account")).status_code, 401)
        self.assertEqual(
            self.client.post(reverse("api-account-password"), {}).status_code, 401
        )


class PasswordResetApiTest(TestCase):
    def setUp(self):
        cache.clear()  # throttle counters
        User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")

    def reset(self, email):
        return self.client.post(
            reverse("api-account-password-reset"),
            {"email": email},
            content_type="application/json",
        )

    def test_reset_email_links_to_the_website(self):
        self.assertEqual(self.reset("jdoe@example.com").status_code, 204)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["jdoe@example.com"])
        self.assertIn("https://", mail.outbox[0].body)
        self.assertIn("/password-reset/confirm/", mail.outbox[0].body)

    def test_unknown_email_gives_the_same_answer(self):
        self.assertEqual(self.reset("nobody@example.com").status_code, 204)
        self.assertEqual(mail.outbox, [])

    def test_invalid_email_is_rejected(self):
        self.assertIn("email", self.reset("not-an-email").json())

    def test_reset_requests_are_throttled(self):
        statuses = [self.reset("jdoe@example.com").status_code for _ in range(6)]
        self.assertEqual(statuses, [204] * 5 + [429])


class CartApiTest(TestCase):
    def setUp(self):
        self.shirt = create_product(title="Linen Shirt", price=Decimal("12.00"), num_in_stock=3)
        self.book = create_product(title="Cookbook", price=Decimal("5.00"), num_in_stock=10)
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.auth = {"HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"}

    def voucher(self, code="WELCOME10", min_items=1):
        everything = RangeFactory(includes_all_products=True)
        offer = ConditionalOfferFactory(
            offer_type="Voucher",
            condition=ConditionFactory(range=everything, type="Count", value=min_items),
            benefit=BenefitFactory(range=everything, type="Percentage", value=10),
        )
        voucher = VoucherFactory(code=code)
        voucher.offers.add(offer)
        return voucher

    def add(self, product, quantity=1, client=None, **auth):
        return (client or self.client).post(
            reverse("api-cart-lines"),
            {"product": product.pk, "quantity": quantity},
            content_type="application/json",
            **auth,
        )

    def patch(self, line_id, quantity):
        return self.client.patch(
            reverse("api-cart-line", args=[line_id]),
            {"quantity": quantity},
            content_type="application/json",
            **self.auth,
        )

    def test_guest_cart_with_products_and_totals(self):
        response = self.add(self.shirt, 2)
        self.assertEqual(response.status_code, 201)
        self.add(self.book)

        cart = self.client.get(reverse("api-cart")).json()
        self.assertEqual(cart["num_items"], 3)
        self.assertEqual(
            [(l["product"]["title"], l["quantity"], l["price_incl_tax"]) for l in cart["lines"]],
            [("Linen Shirt", 2, "24.00"), ("Cookbook", 1, "5.00")],
        )
        self.assertEqual(cart["total_incl_tax"], "29.00")

    def test_stock_is_checked_when_adding_and_changing_quantities(self):
        self.assertEqual(self.add(self.shirt, 2, **self.auth).status_code, 201)
        response = self.add(self.shirt, 2, **self.auth)
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.json())

        line_id = self.client.get(reverse("api-cart"), **self.auth).json()["lines"][0]["id"]
        self.assertEqual(self.patch(line_id, 9).status_code, 400)
        self.assertEqual(self.patch(line_id, 3).json()["lines"][0]["quantity"], 3)

    def test_quantity_0_and_delete_remove_lines(self):
        self.add(self.shirt, **self.auth)
        self.add(self.book, **self.auth)
        lines = self.client.get(reverse("api-cart"), **self.auth).json()["lines"]

        self.assertEqual(len(self.patch(lines[0]["id"], 0).json()["lines"]), 1)
        cart = self.client.delete(reverse("api-cart-line", args=[lines[1]["id"]]), **self.auth)
        self.assertEqual(cart.json()["lines"], [])

    def test_voucher_is_applied_and_removed(self):
        self.voucher()
        self.add(self.shirt, 2, **self.auth)

        cart = self.client.post(
            reverse("api-cart-vouchers"), {"code": "welcome10"},
            content_type="application/json", **self.auth,
        ).json()
        self.assertEqual(cart["total_incl_tax_excl_discounts"], "24.00")
        self.assertEqual(cart["total_incl_tax"], "21.60")
        self.assertEqual([(v["code"], v["amount"]) for v in cart["vouchers"]], [("WELCOME10", "2.40")])

        cart = self.client.delete(reverse("api-cart-voucher", args=["WELCOME10"]), **self.auth).json()
        self.assertEqual(cart["vouchers"], [])
        self.assertEqual(cart["total_incl_tax"], "24.00")

    def test_voucher_errors(self):
        self.voucher(code="BULK", min_items=5)
        self.add(self.book, **self.auth)

        for code, error in (("NOPE", "Voucher code unknown"),
                            ("BULK", "Your basket does not qualify for a voucher discount")):
            response = self.client.post(
                reverse("api-cart-vouchers"), {"code": code},
                content_type="application/json", **self.auth,
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["non_field_errors"], [error])

    def test_guest_cart_is_merged_into_the_account_cart(self):
        self.add(self.book, **self.auth)
        guest = Client()  # keeps the session cookie, like the app
        self.add(self.shirt, 2, client=guest)

        cart = guest.get(reverse("api-cart"), **self.auth).json()
        self.assertEqual(
            sorted((l["product"]["title"], l["quantity"]) for l in cart["lines"]),
            [("Cookbook", 1), ("Linen Shirt", 2)],
        )
        # merged once: the guest basket is gone
        self.assertEqual(guest.get(reverse("api-cart"), **self.auth).json()["num_items"], 3)

    def test_accounts_do_not_share_carts(self):
        self.add(self.shirt, **self.auth)
        other = User.objects.create_user("other", "other@example.com", "s3cret-pass")
        other_auth = {"HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=other).key}"}

        self.assertEqual(Client().get(reverse("api-cart"), **other_auth).json()["lines"], [])
        line_id = self.client.get(reverse("api-cart"), **self.auth).json()["lines"][0]["id"]
        response = Client().delete(reverse("api-cart-line", args=[line_id]), **other_auth)
        self.assertEqual(response.status_code, 404)

    def test_failed_first_guest_request_answers_json(self):
        # the session is not saved during the (rolled back) request
        response = Client().post(
            reverse("api-cart-lines"), {"product": 999999, "quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "application/json")


class WebAppOriginTest(TestCase):
    """The Flutter web app shares the website origin (/app/)"""

    def test_website_session_does_not_trigger_csrf_on_the_api(self):
        user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(user)  # signed in on the website

        response = browser.post(
            reverse("api-register"),
            {
                "email": "new@example.com",
                "password1": "Sup3r-secret-42",
                "password2": "Sup3r-secret-42",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_guest_cart_still_uses_the_session(self):
        product = create_product(title="Book", price=Decimal("5.00"), num_in_stock=3)
        browser = Client(enforce_csrf_checks=True)
        response = browser.post(
            reverse("api-cart-lines"), {"product": product.pk, "quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(browser.get(reverse("api-cart")).json()["num_items"], 1)


class WishlistApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("jdoe", "jdoe@example.com", "s3cret-pass")
        self.auth = {
            "HTTP_AUTHORIZATION": f"Token {Token.objects.create(user=self.user).key}"
        }
        self.shirt = create_product(title="Shirt", price=12, num_in_stock=3)
        self.book = create_product(title="Book", price=5, num_in_stock=1)

    def add(self, product_id, **auth):
        return self.client.post(
            reverse("api-wishlist"), {"product": product_id},
            content_type="application/json", **(auth or self.auth),
        )

    def listed(self):
        response = self.client.get(reverse("api-wishlist"), **self.auth)
        self.assertEqual(response.status_code, 200)
        return [p["id"] for p in response.json()]

    def test_empty_wishlist_is_not_created_by_listing(self):
        self.assertEqual(self.listed(), [])
        self.assertFalse(self.user.wishlists.exists())

    def test_add_list_and_remove_products(self):
        response = self.add(self.shirt.pk)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["price"]["excl_tax"], "12.00")
        self.add(self.book.pk)
        self.assertEqual(self.listed(), [self.book.pk, self.shirt.pk])

        response = self.client.delete(
            reverse("api-wishlist-item", args=[self.book.pk]), **self.auth
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.listed(), [self.shirt.pk])
        # removing a product that is not there is not an error
        response = self.client.delete(
            reverse("api-wishlist-item", args=[self.book.pk]), **self.auth
        )
        self.assertEqual(response.status_code, 204)

    def test_adding_twice_keeps_one_line(self):
        self.assertEqual(self.add(self.shirt.pk).status_code, 201)
        self.assertEqual(self.add(self.shirt.pk).status_code, 200)
        self.assertEqual(self.user.wishlists.get().lines.count(), 1)

    def test_uses_the_wishlist_of_the_website(self):
        website = self.user.wishlists.create(name="Birthday")
        website.add(self.book)
        self.add(self.shirt.pk)
        self.assertEqual(self.user.wishlists.count(), 1)
        self.assertEqual(self.listed(), [self.shirt.pk, self.book.pk])

    def test_other_users_wishlists_are_hidden(self):
        other = User.objects.create_user("other", "other@example.com", "s3cret-pass")
        other.wishlists.create().add(self.book)
        self.assertEqual(self.listed(), [])

    def test_unknown_product_is_refused(self):
        self.assertEqual(self.add(999999).status_code, 404)
        self.assertEqual(self.add("abc").status_code, 400)

    def test_wishlist_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("api-wishlist")).status_code, 401)
        response = self.client.post(
            reverse("api-wishlist"), {"product": self.shirt.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
