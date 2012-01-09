from django.conf.urls.defaults import patterns, url, include

from oscar.core.application import Application
from oscar.apps.catalogue.views import ProductDetailView, ProductListView, ProductCategoryView
from oscar.apps.catalogue.reviews.app import application as reviews_app


class BaseCatalogueApplication(Application):
    name = 'catalogue'
    detail_view = ProductDetailView
    index_view = ProductListView
    category_view = ProductCategoryView
    
    def get_urls(self):
        urlpatterns = super(BaseCatalogueApplication, self).get_urls()        
        urlpatterns += patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),       
            url(r'^(?P<product_slug>[\w-]*)-(?P<pk>\d+)/$', self.detail_view.as_view(), name='detail'),
            url(r'^(?P<category_slug>[\w-]+(/[\w-]+)*)/$', self.category_view.as_view(), name='category')
        )
        return self.post_process_urls(urlpatterns)


class ReviewsApplication(Application):
    reviews_app = reviews_app    
    
    def get_urls(self):
        urlpatterns = super(ReviewsApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^(?P<product_slug>[\w-]*)-(?P<product_pk>\d+)/reviews/', include(self.reviews_app.urls)),
        )
        return self.post_process_urls(urlpatterns)


class CatalogueApplication(BaseCatalogueApplication, ReviewsApplication):
    """
    Composite class combining Products with Reviews
    """

application = CatalogueApplication()