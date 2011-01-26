from django.conf.urls.defaults import *
from oscar.views import home

urlpatterns = patterns('',
    (r'^$', home),                   
    (r'product/', include('oscar.product.urls')),
    (r'basket/', include('oscar.basket.urls')),
    (r'checkout/', include('oscar.checkout.urls')),
)
