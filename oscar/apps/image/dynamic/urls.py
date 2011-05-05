from django.conf.urls.defaults import *
from oscar.apps.image.dynamic import DjangoImageHandler

resizer = DjangoImageHandler()

urlpatterns = patterns('',
    (r'^.*$', resizer),
)
