from oscar.core.application import Application
from oscar.apps.product.views import ItemDetailView, ItemClassListView, ProductListView
from django.conf.urls.defaults import patterns, url, include
from oscar.apps.product.reviews import application as reviews_app

class ProductApplication(Application):
    name = 'products'
    detail_view = ItemDetailView
    class_list_view = ItemClassListView
    list_view = ProductListView
    reviews_app = reviews_app    

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='list'),
            url(r'^(?P<item_class_slug>[\w-]+)/$', self.class_list_view.as_view(), name='class-list'),            
            url(r'^(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<pk>\d+)/$', self.detail_view.as_view(), name='detail'),
            url(r'^(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_pk>\d+)/reviews/', include(self.reviews_app.urls)), 
        )
        return urlpatterns

class ProductWithReviewsApplication(ProductApplication):
    def get_urls(self):
        urlpatterns = super(ProductWithReviewsApplication, self).get_urls()
        mypatterns = patterns('',
            
        )
        return urlpatterns + mypatterns 

application = ProductApplication()