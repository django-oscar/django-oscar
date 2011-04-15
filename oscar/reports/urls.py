from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.reports.views',
    url(r'^$', 'dashboard', name='oscar-report-dashboard'),
)
