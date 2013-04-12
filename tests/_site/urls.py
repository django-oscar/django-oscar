from django.conf.urls import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from oscar.app import shop


urlpatterns = patterns('',
    (r'', include(shop.urls)),
)
urlpatterns += staticfiles_urlpatterns()
