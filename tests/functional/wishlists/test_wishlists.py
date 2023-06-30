from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from oscar.apps.wishlists.models import WishList, WishListSharedEmail
from oscar.test.factories import WishListFactory
from oscar.test.testcases import WebTestCase

User = get_user_model()


class WishListPrivateTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            email="test@example.com", password="testpassword"
        )
        self.wishlist = WishListFactory(owner=self.user, visibility=WishList.PRIVATE)
        self.wishlist_shared_url = self.wishlist.get_shared_url()

    def test_private_wishlist_detail_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_private_wishlist_detail_logged_out_user(self):
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 403)

    def test_private_wishlist_detail_shared_email(self):
        WishListSharedEmail.objects.create(
            wishlist=self.wishlist, email="test2@example.com"
        )
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(
            response.status_code,
            403,
            "The response should be 403 because the visibility is set to private.",
        )

    def test_private_wishlist_is_sharable(self):
        self.assertFalse(self.wishlist.is_shareable)


class WishListPublicTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            email="test@example.com", password="testpassword"
        )
        self.wishlist = WishListFactory(owner=self.user, visibility=WishList.PUBLIC)
        self.wishlist_shared_url = self.wishlist.get_shared_url()

    def test_public_wishlist_detail_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_public_wishlist_detail_logged_out_user(self):
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_public_wishlist_detail_shared_email(self):
        WishListSharedEmail.objects.create(
            wishlist=self.wishlist, email="test2@example.com"
        )
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_public_wishlist_is_sharable(self):
        self.assertTrue(self.wishlist.is_shareable)


class WishListSharedTestCase(WebTestCase):
    def setUp(self):
        super().setUp()
        self.wishlist_user = User.objects.create(
            email="test@example.com", password="testpassword"
        )
        self.wishlist = WishListFactory(
            owner=self.wishlist_user, visibility=WishList.SHARED
        )
        self.wishlist_shared_url = self.wishlist.get_shared_url()

    def test_shared_wishlist_detail_owner(self):
        self.client.force_login(self.wishlist_user)
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_shared_wishlist_detail_logged_out_user(self):
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 302)

    def test_shared_wishlist_detail_shared_email(self):
        WishListSharedEmail.objects.create(
            wishlist=self.wishlist, email="test2@example.com"
        )
        user = User.objects.create(
            email="test2@example.com", password="testpassword", username="test2"
        )
        self.client.force_login(user)
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 200)

    def test_shared_wishlist_detail_non_shared_logged_in_user(self):
        # Create and set a user that has no access to the wishlist
        non_shared_user = User.objects.create(
            email="anotheruser@example.com",
            password="testpassword",
            username="anotheruser",
        )
        self.client.force_login(non_shared_user)
        response = self.client.get(self.wishlist_shared_url)
        self.assertEqual(response.status_code, 403)

    @override_settings(LOGIN_URL=reverse("customer:login"))
    def test_shared_wishlist_detail_non_authenticated_user(self):
        user = User.objects.create(email="test2@example.com", username="test2")
        user.set_password("testpassword")
        user.save()
        WishListSharedEmail.objects.create(
            wishlist=self.wishlist, email="test2@example.com"
        )

        # Set user to None (non authenticated user)
        self.user = None

        response = self.get(self.wishlist_shared_url)
        self.assertIsRedirect(response)

        form = response.follow().forms["login_form"]
        form["login-username"] = "test2@example.com"
        form["login-password"] = "testpassword"
        response = form.submit("login_submit").follow()
        self.assertEqual(response.request.path, self.wishlist_shared_url)

    def test_shared_wishlist_is_sharable(self):
        self.assertTrue(self.wishlist.is_shareable)
