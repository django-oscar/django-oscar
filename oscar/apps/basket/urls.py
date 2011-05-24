from django.conf.urls.defaults import patterns, url
from oscar.apps.basket.views import BasketView, SavedBasketView

urlpatterns = patterns('',
    url(r'saved/$', SavedBasketView.as_view(), name='oscar-basket-saved'),                       
    url(r'^$', BasketView.as_view(), name='oscar-basket'),
)
