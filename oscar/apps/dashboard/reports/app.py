from django.conf.urls import patterns, url

from oscar.core.application import DashboardApplication
from oscar.apps.dashboard.reports import views


class ReportsApplication(DashboardApplication):
    name = None

    index_view = views.IndexView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='reports-index'),
        )
        return self.post_process_urls(urlpatterns)


application = ReportsApplication()
