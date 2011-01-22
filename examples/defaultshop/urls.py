from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import redirect_to

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', redirect_to, {'url': '/shop/'}),                   
    (r'^shop/', include('oscar.urls')),
    (r'^admin/', include(admin.site.urls)),
)
