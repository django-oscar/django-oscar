from django.conf.urls.defaults import patterns, url
from oscar.apps.basket.views import NewBasketView, SavedBasketView

urlpatterns = patterns('',
    url(r'saved/$', SavedBasketView.as_view(), name='oscar-basket-saved'),                       
    url(r'^$', NewBasketView.as_view(), name='oscar-basket'),
)
