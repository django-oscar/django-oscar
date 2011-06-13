from django.conf.urls.defaults import *

from oscar.core.loading import import_module
import_module('basket.views', ['BasketView', 'LineView', 'SavedLineView'], locals())

urlpatterns = patterns('oscar.basket.views',
    url(r'^line/(?P<line_reference>[\w-]+)/$', LineView.as_view(), name='oscar-basket-line'),
    url(r'^saved-line/(?P<line_reference>[\w-]+)/$', SavedLineView.as_view(), name='oscar-saved-basket-line'),
    url(r'^$', BasketView.as_view(), name='oscar-basket'),
)

