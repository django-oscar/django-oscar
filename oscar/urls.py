from django.conf.urls.defaults import *
from oscar.views import home

urlpatterns = patterns('',
    (r'product/', include('oscar.product.urls')),
    (r'basket/', include('oscar.basket.urls')),
    (r'checkout/', include('oscar.checkout.urls')),
    (r'order-management/', include('oscar.order_management.urls')),
    (r'accounts/', include('oscar.customer.urls')),
    (r'^$', home),     
)
