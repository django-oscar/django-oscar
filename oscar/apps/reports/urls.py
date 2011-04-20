from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.apps.reports.views',
    url(r'^$', 'dashboard', name='oscar-report-dashboard'),
)
