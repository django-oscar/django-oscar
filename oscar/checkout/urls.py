from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.checkout.views',
    url(r'$', 'index', name='oscar-checkout-index'),
)
