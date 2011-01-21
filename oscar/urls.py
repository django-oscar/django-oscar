from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'product/', include('oscar.product.urls')),
    (r'basket/', include('oscar.basket.urls')),
)
