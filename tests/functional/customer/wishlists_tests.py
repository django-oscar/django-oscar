# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

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

    def test_wishlists_form_does_not_exist(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['wishlists']):
            detail_page = self.get(self.product.get_absolute_url())

        self.assertFalse('add_to_wishlist_form' in detail_page.forms)


class TestProfilePage(WebTestCase):
    is_anonymous = False

    def test_wishlists_link_exists(self):
        """
        Because of differences between src/oscar/templates/oscar/layout.html
        and tests/_site/templates/layout.html, this test will always fail.

        See https://github.com/django-oscar/django-oscar/issues/1991 for
        a complete explanation.

        Feel free to uncomment the body of this method when that issue has
        been resolved.
        """
#        account_page = self.get(reverse('customer:profile-view'))
#
#        with open('/Users/zmott/Desktop/test.html', 'wb') as outfile:
#            outfile.write(account_page.content)
#
#        html = account_page.content.decode('utf-8')
#        self.assertTrue(reverse('customer:wishlists-list') in html)

    def test_wishlists_link_does_not_exist(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['wishlists']):
            account_page = self.get(reverse('customer:profile-view'))

        html = account_page.content.decode('utf-8')
        self.assertFalse(reverse('customer:wishlists-list') in html)
