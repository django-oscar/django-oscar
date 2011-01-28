from django.conf.urls.defaults import *

from oscar.basket.views import LineView

def constructLineView(request, *args, **kwargs):
    return LineView()(request, *args, **kwargs)

urlpatterns = patterns('oscar.basket.views',
    url(r'line/(?P<line_reference>\w+)/$', constructLineView, name='oscar-basket-line'),
    url(r'^$', 'index', name='oscar-basket'),
)
