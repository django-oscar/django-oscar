from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
import_module('product.reviews.views', ['CreateProductReviewView', 'ProductReviewDetailView',
                                        'ProductReviewListView'], locals())  

urlpatterns = patterns('oscar.product.reviews.views',
    url(r'(?P<pk>\d+)/$', ProductReviewDetailView.as_view(), name='oscar-product-review'),
    url(r'add/$', CreateProductReviewView.as_view(), name='oscar-product-review-add'),
    url(r'all/$', ProductReviewListView.as_view(), name='oscar-product-reviews'),
)
