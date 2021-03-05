from django.conf import settings
from django.urls import reverse

from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase


class TestHiddenFeatures(WebTestCase):
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.product = create_product()
        self.wishlists_url = reverse('customer:wishlists-list')
        self.installed_apps_setting = settings.INSTALLED_APPS.copy()

    def test_reviews_enabled(self):
        product_detail_page = self.get(self.product.get_absolute_url())
        self.assertContains(product_detail_page, 'Number of reviews')

    def test_reviews_disabled(self):
        self.installed_apps_setting.remove('oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig')
        with self.settings(INSTALLED_APPS=self.installed_apps_setting):
            product_detail_page = self.get(self.product.get_absolute_url())
            self.assertNotContains(product_detail_page, 'Number of reviews')

    def test_wishlists_enabled(self):
        account_page = self.get(reverse('customer:profile-view'))
        self.assertContains(account_page, self.wishlists_url)
        product_detail_page = self.get(self.product.get_absolute_url())
        self.assertContains(product_detail_page, 'Add to wish list')

    def test_wishlists_disabled(self):
        self.installed_apps_setting.remove('oscar.apps.wishlists.apps.WishlistsConfig')
        with self.settings(INSTALLED_APPS=self.installed_apps_setting):
            account_page = self.get(reverse('customer:profile-view'))

            self.assertNotContains(account_page, self.wishlists_url)
            product_detail_page = self.get(self.product.get_absolute_url())
            self.assertNotContains(product_detail_page, 'Add to wish list')
