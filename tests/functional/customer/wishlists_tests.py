# -*- coding: utf-8 -*-
from oscar.core.loading import get_model

from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase

WishList = get_model('wishlists', 'WishList')


class TestProductDetailPage(WebTestCase):
    is_anonymous = False

    def setUp(self):
        super(TestProductDetailPage, self).setUp()
        self.product = create_product()

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
