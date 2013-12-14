from django.conf.urls import patterns, url, include

from oscar.core.application import Application
from oscar.apps.catalogue import views
from oscar.apps.offer import views as offer_views
from oscar.apps.catalogue.reviews.app import application as reviews_app


class BaseCatalogueApplication(Application):
    name = 'catalogue'
    detail_view = views.ProductDetailView
    index_view = views.ProductListView
    category_view = views.ProductCategoryView
    range_view = offer_views.RangeDetailView

    def get_urls(self):
        urlpatterns = super(BaseCatalogueApplication, self).get_urls()
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$',
                self.detail_view.as_view(), name='detail'),
            url(r'^category/(?P<category_slug>[\w-]+(/[\w-]+)*)_(?P<pk>\d+)/$',
                self.category_view.as_view(), name='category'),
            url(r'^ranges/(?P<slug>[\w-]+)/$',
                self.range_view.as_view(), name='range'),
            # Legacy route for the category view
            url(r'^(?P<category_slug>[\w-]+(/[\w-]+)*)/$',
                self.category_view.as_view(), name='category')]
        urlpatterns += patterns('', *urls)
        return self.post_process_urls(urlpatterns)


class ReviewsApplication(Application):
    name = None
    reviews_app = reviews_app

    def get_urls(self):
        urlpatterns = super(ReviewsApplication, self).get_urls()
        urls = [
            url(r'^(?P<product_slug>[\w-]*)_(?P<product_pk>\d+)/reviews/',
                include(self.reviews_app.urls)),
        ]
        urlpatterns += patterns('', *urls)
        return self.post_process_urls(urlpatterns)


class CatalogueApplication(BaseCatalogueApplication, ReviewsApplication):
    """
    Composite class combining Products with Reviews
    """


application = CatalogueApplication()
