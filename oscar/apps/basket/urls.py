from django.conf.urls.defaults import *

from oscar.apps.basket.views import BasketView, LineView, SavedLineView

def line_view(request, *args, **kwargs):
    return LineView()(request, *args, **kwargs)

def saved_line_view(request, *args, **kwargs):
    return SavedLineView()(request, *args, **kwargs)

def basket_view(request, *args, **kwargs):
    return BasketView()(request, *args, **kwargs)

urlpatterns = patterns('oscar.basket.views',
    url(r'^line/(?P<line_reference>[\w-]+)/$', line_view, name='oscar-basket-line'),
    url(r'^saved-line/(?P<line_reference>[\w-]+)/$', saved_line_view, name='oscar-saved-basket-line'),
    url(r'^$', basket_view, name='oscar-basket'),
)
