from django.conf.urls.defaults import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.catalogue.views import ProductListView


class CatalogueApplication(Application):
    name = None
    product_list_view = ProductListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.product_list_view.as_view(),
                name='catalogue-product-list'),
        )
        return self.post_process_urls(urlpatterns)


application = CatalogueApplication()
