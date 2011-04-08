from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.promotions.views',
    url(r'redirect/(?P<page_promotion_id>\d+)/$', 'promotion_click', name='oscar-promotion-click'),
)
