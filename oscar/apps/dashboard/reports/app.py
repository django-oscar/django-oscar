from django.conf.urls import url

from oscar.core.application import Application
from oscar.apps.dashboard.reports import views


class ReportsApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    index_view = views.IndexView

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='reports-index'),
        ]
        return self.post_process_urls(urls)


application = ReportsApplication()
