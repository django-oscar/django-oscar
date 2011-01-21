from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^shop/', include('oscar.urls')),
    (r'^admin/', include(admin.site.urls)),
)
