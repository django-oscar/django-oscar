from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from haystack.query import SearchQuerySet

from oscar.core.application import Application
from oscar.apps.reports.views import DashboardView


class ReportsApplication(Application):
    name = 'reports'
    
    dashboard_view = DashboardView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', staff_member_required(self.dashboard_view.as_view()), name='dashboard'),
        )
        return self.post_process_urls(urlpatterns)


application = ReportsApplication()