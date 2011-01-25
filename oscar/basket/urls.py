from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.basket.views',
    url(r'line/(?P<line_reference>\w+)/$', 'line', name='oscar-basket-line'),
    url(r'^$', 'index', name='oscar-basket'),
)
