from oscar.core.application import Application
from oscar.apps.product.views import ItemDetailView, ProductListView, CategoryView
from django.conf.urls.defaults import patterns, url, include
from oscar.apps.product.reviews.app import application as reviews_app


class BaseProductApplication(Application):
    name = 'products'
    detail_view = ItemDetailView
    list_view = ProductListView
    category_view = CategoryView
    
    def get_urls(self):
        urlpatterns = super(BaseProductApplication, self).get_urls()        
        urlpatterns += patterns('',
            url(r'^$', self.list_view.as_view(), name='list'),       
            url(r'^(?P<item_slug>[\w-]*)-(?P<pk>\d+)/$', self.detail_view.as_view(), name='detail'),
            url(r'^(?P<category_slug>[\w-]+(/[\w-]+)*)/$', self.category_view.as_view(), name='category')
        )
        return urlpatterns


class ReviewsApplication(Application):
    reviews_app = reviews_app    
    
    def get_urls(self):
        urlpatterns = super(ReviewsApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^(?P<item_slug>[\w-]*)-(?P<item_pk>\d+)/reviews/', include(self.reviews_app.urls)),
        )
        return urlpatterns
    

class NavigationApplication(Application):
    backend = None
    
    def get_urls(self):
        urlpatterns = super(NavigationApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^', include(self.backend.urls))
        )
        return urlpatterns


class ProductApplication(BaseProductApplication, ReviewsApplication):
    """
    Composite class combining Products with Reviews
    """

application = ProductApplication()