from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
import_module('basket.views', ['BasketView', 'LineView', 'SavedLineView'], locals())

from oscar.apps.basket.views import NewBasketView

urlpatterns = patterns('oscar.basket.views',
    url(r'^line/(?P<line_reference>[\w-]+)/$', class_based_view(LineView), name='oscar-basket-line'),
    url(r'^saved-line/(?P<line_reference>[\w-]+)/$', class_based_view(SavedLineView), name='oscar-saved-basket-line'),
    url(r'^$', class_based_view(BasketView), name='oscar-basket'),
    url(r'new/$', NewBasketView.as_view(), name='oscar-newbasket'),
)

