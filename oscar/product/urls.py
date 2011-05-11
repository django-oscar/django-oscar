from django.conf.urls.defaults import *
from oscar.product.views import ItemDetailView, ProductListView, ItemClassListView, ItemReviewView, ReviewDetailView, ReviewListView, ReviewVoteView
from oscar.views import class_based_view

urlpatterns = patterns('oscar.product.views',
    #product reviews stuff
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/review/(?P<review_id>\d+)/$', ReviewDetailView.as_view(), name='oscar-product-review'),
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/reviews/$', ReviewListView.as_view(), name='oscar-product-reviews'),
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/add-review/$', class_based_view(ItemReviewView), name='oscar-product-review-add'),
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/review/(?P<review_id>\d+)/$', ReviewVoteView.as_view(), name='oscar-vote-review'),    
    #basic product item stuff
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/$', ItemDetailView.as_view(), name='oscar-product-item'),    
    url(r'(?P<item_class_slug>[\w-]+)/$', ItemClassListView.as_view(), name='oscar-product-item-class'),
    url(r'^$', ProductListView.as_view(), name='oscar-products'),
)
