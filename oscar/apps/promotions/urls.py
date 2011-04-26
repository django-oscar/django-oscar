from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
promotion_views = import_module('promotions.views', ['HomeView'])

urlpatterns = patterns('oscar.apps.promotions.views',
    url(r'page-redirect/(?P<page_promotion_id>\d+)/$', 'page_promotion_click', name='oscar-page-promotion-click'),
    url(r'keyword-redirect/(?P<keyword_promotion_id>\d+)/$', 'keyword_promotion_click', name='oscar-keyword-promotion-click'),
    url(r'$', class_based_view(promotion_views.HomeView), name='oscar-home'),
)
