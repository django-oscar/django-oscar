# -*- coding: utf-8 -*-
from django.urls import reverse_lazy

from oscar.core.loading import get_model

from oscar.test.factories import create_product, WishListFactory
from oscar.test.testcases import WebTestCase

WishList = get_model('wishlists', 'WishList')


class WishListTestMixin(object):
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.product = create_product()


class TestProductDetailPage(WishListTestMixin, WebTestCase):

    def test_allows_a_product_to_be_added_to_wishlist(self):
        # Click add to wishlist button
        detail_page = self.get(self.product.get_absolute_url())
        form = detail_page.forms['add_to_wishlist_form']
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
        url = reverse_lazy('customer:wishlists-move-product-to-another', kwargs={'key': self.wishlist1.key,
                                                                                 'line_pk': line1.pk,
                                                                                 'to_key': self.wishlist2.key})
        self.get(url)
        self.assertEqual(self.wishlist1.lines.filter(product=self.product).count(), 1)
        self.assertEqual(self.wishlist2.lines.filter(product=self.product).count(), 1)

    def test_move_product_to_another_wishlist(self):
        self.wishlist1.add(self.product)
        line1 = self.wishlist1.lines.get(product=self.product)
        url = reverse_lazy('customer:wishlists-move-product-to-another', kwargs={'key': self.wishlist1.key,
                                                                                 'line_pk': line1.pk,
                                                                                 'to_key': self.wishlist2.key})
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
            'customer:wishlists-remove-product', kwargs={'key': self.wishlist.key, 'line_pk': self.line.pk}
        )
        self.get(delete_wishlist_line_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(delete_wishlist_line_url, expect_errors=True).status_code, 404)

    def test_remove_wishlist_product(self):
        delete_wishlist_product_url = reverse_lazy(
            'customer:wishlists-remove-product', kwargs={'key': self.wishlist.key, 'product_pk': self.line.product.id}
        )
        self.get(delete_wishlist_product_url).forms[0].submit()
        # Test WishList doesnt contain line and return 404
        self.assertEqual(self.get(delete_wishlist_product_url, expect_errors=True).status_code, 404)
