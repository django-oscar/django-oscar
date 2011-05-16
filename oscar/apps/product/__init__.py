from django.conf.urls.defaults import patterns, url, include        
from oscar.core.application import Application
from oscar.apps.product.views import ItemDetailView, ItemClassListView, ProductListView


class ProductApplication(Application):
    name = 'products'
    detail_view = ItemDetailView
    class_list_view = ItemClassListView
    list_view = ProductListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='list'),
            url(r'^(?P<item_class_slug>[\w-]+)/$', self.class_list_view.as_view(), name='class-list'),            
            url(r'^(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<pk>\d+)/$', self.detail_view.as_view(), name='detail'),
        )
        return urlpatterns


application = ProductApplication()