from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.utils.six.moves import http_client

from oscar.apps.catalogue.models import Category
from oscar.test.decorators import ignore_deprecation_warnings
from oscar.test.testcases import WebTestCase

from oscar.test.factories import create_product


class TestProductDetailView(WebTestCase):

    def test_enforces_canonical_url(self):
        p = create_product()
        kwargs = {'product_slug': '1_wrong-but-valid-slug_1',
                  'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(p.get_absolute_url() in response.location)

    def test_child_to_parent_redirect(self):
        parent_product = create_product(structure='parent')
        kwargs = {'product_slug': parent_product.slug,
                  'pk': parent_product.id}
        parent_product_url = reverse('catalogue:detail', kwargs=kwargs)

        child = create_product(
            title="Variant 1", structure='child', parent=parent_product)
        kwargs = {'product_slug': child.slug,
                  'pk': child.id}
        child_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(parent_product_url)
        self.assertEqual(http_client.OK, response.status_code)

        response = self.app.get(child_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)


class TestProductListView(WebTestCase):

    def test_shows_add_to_basket_button_for_available_product(self):
        product = create_product(num_in_stock=1)
        page = self.app.get(reverse('catalogue:index'))
        self.assertContains(page, product.title)
        self.assertContains(page, ugettext("Add to basket"))

    def test_shows_not_available_for_out_of_stock_product(self):
        product = create_product(num_in_stock=0)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, product.title)
        self.assertContains(page, "Unavailable")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = settings.OSCAR_PRODUCTS_PER_PAGE
        title = u"Product #%d"
        for idx in range(0, int(1.5 * per_page)):
            create_product(title=title % idx)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, "Page 1 of 2")


class TestProductCategoryView(WebTestCase):

    def setUp(self):
        self.category = Category.add_root(name="Products")

    def test_browsing_works(self):
        correct_url = self.category.get_absolute_url()
        response = self.app.get(correct_url)
        self.assertEqual(http_client.OK, response.status_code)

    def test_enforces_canonical_url(self):
        kwargs = {'category_slug': '1_wrong-but-valid-slug_1',
                  'pk': self.category.pk}
        wrong_url = reverse('catalogue:category', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(self.category.get_absolute_url() in response.location)

    @ignore_deprecation_warnings
    def test_can_chop_off_last_part_of_url(self):
        # We cache category URLs, which normally is a safe thing to do, as
        # the primary key stays the same and ProductCategoryView only looks
        # at the key any way.
        # But this test chops the URLs, and hence relies on the URLs being
        # correct. So in this case, we start with a clean cache to ensure
        # our URLs are correct.
        cache.clear()

        child_category = self.category.add_child(name='Cool products')
        full_url = child_category.get_absolute_url()
        chopped_url = full_url.rsplit('/', 2)[0]
        parent_url = self.category.get_absolute_url()
        response = self.app.get(chopped_url).follow()  # fails if no redirect
        self.assertTrue(response.url.endswith(parent_url))
