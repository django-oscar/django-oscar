# -*- coding: utf-8 -*-
from django.urls import reverse_lazy

from oscar.core.loading import get_model
from oscar.test.factories import WishListFactory, create_product
from oscar.test.testcases import WebTestCase

WishList = get_model("wishlists", "WishList")


class WishListTestMixin(object):
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.product = create_product()


class TestProductDetailPage(WishListTestMixin, WebTestCase):
    def test_allows_a_product_to_be_added_to_wishlist(self):
        # Click add to wishlist button
        detail_page = self.get(self.product.get_absolute_url())
        form = detail_page.forms["add_to_wishlist_form"]
        response = form.submit()
        self.assertIsRedirect(response)

        # Check a wishlist has been created
        wishlists = self.user.wishlists.all()
        self.assertEqual(1, len(wishlists))

        lines = wishlists[0].lines.all()
        self.assertEqual(1, len(lines))
        self.assertEqual(self.product, lines[0].product)


class TestMoveProductToAnotherWishList(WishListTestMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        self.wishlist1 = WishListFactory(owner=self.user)
        self.wishlist2 = WishListFactory(owner=self.user)

    def test_move_product_to_another_wishlist_already_containing_it(self):
        self.wishlist1.add(self.product)
        line1 = self.wishlist1.lines.get(product=self.product)
        self.wishlist2.add(self.product)
        url = reverse_lazy(
            "customer:wishlists-move-product-to-another",
            kwargs={
                "key": self.wishlist1.key,
                "line_pk": line1.pk,
                "to_key": self.wishlist2.key,
            },
        )
        self.get(url)
        self.assertEqual(self.wishlist1.lines.filter(product=self.product).count(), 1)
        self.assertEqual(self.wishlist2.lines.filter(product=self.product).count(), 1)

    def test_move_product_to_another_wishlist(self):
        self.wishlist1.add(self.product)
        line1 = self.wishlist1.lines.get(product=self.product)
        url = reverse_lazy(
            "customer:wishlists-move-product-to-another",
            kwargs={
                "key": self.wishlist1.key,
                "line_pk": line1.pk,
                "to_key": self.wishlist2.key,
            },
        )
        self.get(url)
        self.assertEqual(self.wishlist1.lines.filter(product=self.product).count(), 0)
        self.assertEqual(self.wishlist2.lines.filter(product=self.product).count(), 1)
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(url, expect_errors=True).status_code, 404)


class TestWishListRemoveProduct(WishListTestMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        self.wishlist = WishListFactory(owner=self.user)
        self.wishlist.add(self.product)
        self.line = self.wishlist.lines.get(product=self.product)

    def test_remove_wishlist_line(self):
        delete_wishlist_line_url = reverse_lazy(
            "customer:wishlists-remove-product",
            kwargs={"key": self.wishlist.key, "line_pk": self.line.pk},
        )
        self.get(delete_wishlist_line_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(
            self.get(delete_wishlist_line_url, expect_errors=True).status_code, 404
        )

    def test_remove_wishlist_product(self):
        delete_wishlist_product_url = reverse_lazy(
            "customer:wishlists-remove-product",
            kwargs={"key": self.wishlist.key, "product_pk": self.line.product.id},
        )
        self.get(delete_wishlist_product_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(
            self.get(delete_wishlist_product_url, expect_errors=True).status_code, 404
        )


class TestWishListCreateView(WishListTestMixin, WebTestCase):
    def test_create_private_wishlist(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        self.assertEqual(self.user.wishlists.count(), 0)

        form = page.form
        form["name"] = expected_name = "Private wish list"
        form["visibility"] = expected_visibility = WishList.PRIVATE
        form.submit()

        self.assertEqual(self.user.wishlists.count(), 1)

        wishlist = self.user.wishlists.first()
        self.assertEqual(wishlist.name, expected_name)
        self.assertEqual(wishlist.visibility, expected_visibility)

    def test_create_public_wishlist(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        self.assertEqual(self.user.wishlists.count(), 0)

        form = page.form
        form["name"] = expected_name = "Public wish list"
        form["visibility"] = expected_visibility = WishList.PUBLIC
        form.submit()

        self.assertEqual(self.user.wishlists.count(), 1)

        wishlist = self.user.wishlists.first()
        self.assertEqual(wishlist.name, expected_name)
        self.assertEqual(wishlist.visibility, expected_visibility)

    def test_create_shared_wishlist(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        self.assertEqual(self.user.wishlists.count(), 0)

        form = page.form
        form["name"] = expected_name = "Shared wish list"
        form["visibility"] = expected_visibility = WishList.SHARED
        form["shared_emails-0-email"] = shared_email_1 = "test@example.com"
        form["shared_emails-1-email"] = shared_email_2 = "test2@example.com"
        form.submit()

        self.assertEqual(self.user.wishlists.count(), 1)

        wishlist = self.user.wishlists.first()
        self.assertEqual(wishlist.name, expected_name)
        self.assertEqual(wishlist.visibility, expected_visibility)
        self.assertEqual(wishlist.shared_emails.count(), 2)

        shared_emails = wishlist.shared_emails.filter(
            email__in=[shared_email_1, shared_email_2]
        )
        self.assertEqual(shared_emails.count(), 2)

    def test_create_private_wishlist_with_shared_emails(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        form = page.form
        form["name"] = "Private wish list"
        form["visibility"] = WishList.PRIVATE
        form["shared_emails-0-email"] = "test@example.com"
        form["shared_emails-1-email"] = "test2@example.com"
        response = form.submit().follow()

        self.assertTrue(
            "The shared accounts won&#x27;t be able to access your wishlist "
            "because the visiblity is set to private." in response
        )

    def test_create_public_wishlist_with_shared_emails(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        form = page.form
        form["name"] = "Public wish list"
        form["visibility"] = WishList.PUBLIC
        form["shared_emails-0-email"] = "test@example.com"
        form["shared_emails-1-email"] = "test2@example.com"
        response = form.submit().follow()

        self.assertTrue(
            "You have added shared accounts to your wishlist but the visiblity "
            "is public, this means everyone with a link has access to it." in response
        )

    def test_create_wishlist_no_name(self):
        create_wishlist_url = reverse_lazy("customer:wishlists-create")
        page = self.get(create_wishlist_url)

        self.assertEqual(self.user.wishlists.count(), 0)

        form = page.form
        form["name"] = ""
        form["visibility"] = WishList.PUBLIC
        response = form.submit()

        self.assertEqual(self.user.wishlists.count(), 0)
        self.assertTrue("This field is required." in response)


class TestWishListUpdateView(WishListTestMixin, WebTestCase):
    def setUp(self):
        super().setUp()
        self.wishlist = WishListFactory(owner=self.user, name="Test wishlist")

    def test_change_name(self):
        wishlist_update_url = reverse_lazy(
            "customer:wishlists-update", kwargs={"key": self.wishlist.key}
        )
        page = self.get(wishlist_update_url)

        self.assertEqual(self.wishlist.name, "Test wishlist")

        form = page.form
        form["name"] = new_wishlist_name = "Changed wishlist name"
        form.submit()

        self.wishlist.refresh_from_db()
        self.assertEqual(self.wishlist.name, new_wishlist_name)

    def test_change_visibility(self):
        wishlist_update_url = reverse_lazy(
            "customer:wishlists-update", kwargs={"key": self.wishlist.key}
        )
        page = self.get(wishlist_update_url)

        self.assertEqual(self.wishlist.visibility, WishList.PRIVATE)

        form = page.form
        form["visibility"] = new_wishlist_visibility = WishList.PUBLIC
        form.submit()

        self.wishlist.refresh_from_db()
        self.assertEqual(self.wishlist.visibility, new_wishlist_visibility)

    def test_add_shared_email(self):
        wishlist_update_url = reverse_lazy(
            "customer:wishlists-update", kwargs={"key": self.wishlist.key}
        )
        page = self.get(wishlist_update_url)

        self.assertEqual(self.wishlist.shared_emails.count(), 0)

        form = page.form
        form["shared_emails-0-email"] = shared_email_1 = "test@example.com"
        form["shared_emails-1-email"] = shared_email_2 = "test2@example.com"
        form.submit()

        self.wishlist.refresh_from_db()
        self.assertEqual(self.wishlist.shared_emails.count(), 2)
        shared_emails = self.wishlist.shared_emails.filter(
            email__in=[shared_email_1, shared_email_2]
        )
        self.assertEqual(shared_emails.count(), 2)
