from django.conf.urls.defaults import *
from oscar.product.views import ItemDetailView, ProductListView, ItemClassListView, ItemReviewView
from oscar.views import class_based_view

urlpatterns = patterns('oscar.product.views',
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/add-review/$', class_based_view(ItemReviewView), name='oscar-product-review'),
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/$', ItemDetailView.as_view(), name='oscar-product-item'),    
    url(r'(?P<item_class_slug>[\w-]+)/$', ItemClassListView.as_view(), name='oscar-product-item-class'),
    url(r'^$', ProductListView.as_view(), name='oscar-products'),
)
