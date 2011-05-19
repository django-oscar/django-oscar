from django.conf.urls.defaults import *
from oscar.product.views import ItemDetailView, ProductListView, ItemClassListView,\
 ProductReviewView, ProductReviewDetailView, ProductReviewListView, ProductReviewVoteView
from oscar.views import class_based_view

product_url = r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/'

urlpatterns = patterns('oscar.product.views',
    #product reviews stuff
    #url(product_url + r'', simple_view, name='oscar-vote-review'),
    url(product_url + r'review/(?P<review_id>\d+)/vote/$', class_based_view(ProductReviewVoteView), name='oscar-vote-review'),
    url(product_url + r'review/(?P<review_id>\d+)/$', ProductReviewDetailView.as_view(), name='oscar-product-review'),
    url(product_url + r'reviews/$', ProductReviewListView.as_view(), name='oscar-product-reviews'),
    url(product_url + r'add-review/$', class_based_view(ProductReviewView), name='oscar-product-review-add'),
    #basic product item stuff
    url(product_url, ItemDetailView.as_view(), name='oscar-product-item'),    
    url(r'(?P<item_class_slug>[\w-]+)/$', ItemClassListView.as_view(), name='oscar-product-item-class'),
    url(r'^$', ProductListView.as_view(), name='oscar-products'),
)
