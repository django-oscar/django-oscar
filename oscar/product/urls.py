from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.product.views',
    url(r'item/(?P<product_id>[\w]*)$', 'item', name='oscar-product-item'),
)
