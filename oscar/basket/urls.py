from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.basket.views',
    url(r'$', 'index', name='oscar-basket'),
)
