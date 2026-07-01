from django.test import TestCase

from oscar.core.loading import get_model
from oscar.templatetags.wishlist_tags import wishlists_containing_product
from oscar.test.factories import ProductFactory, UserFactory, WishListFactory

Wishlist = get_model("wishlists", "Wishlist")


class WishlistTagsTestCase(TestCase):
    def test_wishlists_containing_product(self):
        p1 = ProductFactory()
        p2 = ProductFactory()
        user = UserFactory()
        wishlist1 = WishListFactory(owner=user)
        WishListFactory(owner=user)
        wishlist1.add(p1)

        containing_one = wishlists_containing_product(Wishlist.objects.all(), p1)
        self.assertEqual(len(containing_one), 1)
        self.assertEqual(containing_one[0], wishlist1)
        containing_none = wishlists_containing_product(Wishlist.objects.all(), p2)
        self.assertEqual(len(containing_none), 0)
