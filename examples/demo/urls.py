from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import redirect_to

from django.conf import settings
from oscar.app import Shop
from oscar.apps.catalogue import ProductApplication
from shop.product.views import MyItemDetailView

admin.autodiscover()

shop_app = Shop(product_app=ProductApplication(detail_view=MyItemDetailView))

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'', include(shop_app.urls)),
)


if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
        url(r'^media/(?P<path>.*)$', 'serve', 
            {'document_root': settings.MEDIA_ROOT}),
    )