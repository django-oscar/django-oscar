import httplib

from django.core.urlresolvers import reverse
from oscar_testsupport.testcases import WebTestCase

from oscar_testsupport.factories import create_product
from oscar.apps.catalogue.views import ProductListView


class TestProductDetailView(WebTestCase):

    def test_enforces_canonical_url(self):
        p = create_product()
        kwargs = {'product_slug': 'wrong-slug',
                  'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEquals(httplib.MOVED_PERMANENTLY, response.status_code)

    def test_variant_to_parent_redirect(self):
        parent_product = create_product()
        kwargs = {'product_slug': parent_product.slug,
                  'pk': parent_product.id}
        parent_product_url = reverse('catalogue:detail', kwargs=kwargs)

        variant = create_product(title="Variant 1", parent=parent_product)
        kwargs = {'product_slug': variant.slug,
                  'pk': variant.id}
        variant_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(parent_product_url)
        self.assertEquals(httplib.OK, response.status_code)

        response = self.app.get(variant_url)
        self.assertEquals(httplib.MOVED_PERMANENTLY, response.status_code)


class TestProductListView(WebTestCase):

    def test_shows_add_to_basket_button_for_available_product(self):
        product = create_product()

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, product.title)
        self.assertContains(page, "Add to basket")

    def test_shows_not_available_for_out_of_stock_product(self):
        product = create_product(num_in_stock=0)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, product.title)
        self.assertContains(page, "Not available")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = ProductListView.paginate_by
        title = u"Product #%d"
        for idx in range(0, int(1.5 * per_page)):
            create_product(title=title % idx)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, "Page 1 of 2")
