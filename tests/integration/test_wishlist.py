from django.test import TestCase

from oscar.apps.wishlists.models import WishList
from oscar.core.compat import get_user_model

User = get_user_model()


class TestAWishlist(TestCase):

    def test_can_generate_a_random_key(self):
        key = WishList.random_key(6)
        self.assertTrue(len(key) == 6)


class TestAPublicWishList(TestCase):

    def setUp(self):
        self.wishlist = WishList(visibility=WishList.PUBLIC)

    def test_is_visible_to_anyone(self):
        user = User()
        self.assertTrue(self.wishlist.is_allowed_to_see(user))


class TestASharedWishList(TestCase):

    def setUp(self):
        self.wishlist = WishList(visibility=WishList.SHARED)

    def test_is_visible_to_anyone(self):
        user = User()
        self.assertTrue(self.wishlist.is_allowed_to_see(user))


class TestAPrivateWishList(TestCase):

    def setUp(self):
        self.owner = User(id=1)
        self.another_user = User(id=2)
        self.wishlist = WishList(owner=self.owner)

    def test_is_visible_only_to_its_owner(self):
        self.assertTrue(self.wishlist.is_allowed_to_see(self.owner))
        self.assertFalse(self.wishlist.is_allowed_to_see(self.another_user))

    def test_can_only_be_edited_by_its_owner(self):
        self.assertTrue(self.wishlist.is_allowed_to_edit(self.owner))
        self.assertFalse(self.wishlist.is_allowed_to_edit(self.another_user))
