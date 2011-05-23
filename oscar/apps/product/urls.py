from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
import_module('product.views', ['ItemDetailView', 'ProductListView', 'ItemClassListView'], locals())  # basic product stuffs
import_module('product.views', ['ProductReviewView', 'ProductReviewDetailView',\
                                 'ProductReviewListView', 'ProductReviewVoteView'], locals())  # product review stuff  

product_url = r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/'

urlpatterns = patterns('oscar.product.views',
    #product reviews stuff    
    url(product_url + r'review/(?P<review_id>\d+)/vote/$', class_based_view(ProductReviewVoteView), name='oscar-vote-review'),
    url(product_url + r'review/(?P<review_id>\d+)/$', ProductReviewDetailView.as_view(), name='oscar-product-review'),
    url(product_url + r'reviews/$', ProductReviewListView.as_view(), name='oscar-product-reviews'),
    url(product_url + r'add-review/$', class_based_view(ProductReviewView), name='oscar-product-review-add'),
    #basic product item stuff
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/$', ItemDetailView.as_view(), name='oscar-product-item'),
    url(r'(?P<item_class_slug>[\w-]+)/$', ItemClassListView.as_view(), name='oscar-product-item-class'),
    url(r'^$', ProductListView.as_view(), name='oscar-products'),
)
