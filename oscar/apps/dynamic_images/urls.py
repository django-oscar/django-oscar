from django.conf.urls.defaults import *
from oscar.apps.dynamic_images import DjangoImageHandler

resizer = DjangoImageHandler()

urlpatterns = patterns('',
    (r'^.*$', resizer),
)
