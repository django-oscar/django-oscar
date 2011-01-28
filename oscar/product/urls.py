from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.product.views',
    url(r'(?P<item_class_slug>[\w-]+)/(?P<item_slug>[\w-]*)-(?P<item_id>\d+)/$', 'item', name='oscar-product-item'),
    url(r'(?P<item_class_slug>[\w-]+)/$', 'item_class', name='oscar-product-item-class'),
    url(r'$', 'all', name='oscar-products'),
)
