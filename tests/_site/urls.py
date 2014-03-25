from django.conf.urls import patterns, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from oscar.app import shop

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'', include(shop.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
urlpatterns += staticfiles_urlpatterns()