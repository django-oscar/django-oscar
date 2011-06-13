from django.conf.urls.defaults import *

from oscar.core.loading import import_module
import_module('promotions.views', ['HomeView'], locals())

urlpatterns = patterns('oscar.apps.promotions.views',
    url(r'page-redirect/(?P<page_promotion_id>\d+)/$', 'page_promotion_click', name='oscar-page-promotion-click'),
    url(r'keyword-redirect/(?P<keyword_promotion_id>\d+)/$', 'keyword_promotion_click', name='oscar-keyword-promotion-click'),
    url(r'$', HomeView.as_view(), name='home'),
)
