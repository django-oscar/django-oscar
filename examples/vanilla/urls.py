from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from oscar.app import shop

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'', include(shop.urls)),
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)