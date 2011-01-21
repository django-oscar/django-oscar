from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'product/', include('oscar.product.urls')),
)
