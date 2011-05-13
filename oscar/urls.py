from django.conf.urls.defaults import *
from django.conf import settings

from oscar.apps.product import application as products_app

urlpatterns = patterns('',
    (r'products/', include(products_app.urls)),
    (r'basket/', include('oscar.apps.basket.urls')),
    (r'checkout/', include('oscar.apps.checkout.urls')),
    (r'order-management/', include('oscar.apps.order_management.urls')),
    (r'accounts/', include('oscar.apps.customer.urls')),
    (r'promotions/', include('oscar.apps.promotions.urls')),
    (r'reports/', include('oscar.apps.reports.urls')),
    (r'search/', include('oscar.apps.search.urls')),
    (r'^$', include('oscar.apps.promotions.urls')),     
)

if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        url(r'^media/(?P<path>.*)$', 'serve', 
            {'document_root': settings.MEDIA_ROOT}),
    )