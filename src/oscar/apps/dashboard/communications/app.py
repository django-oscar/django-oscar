from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class CommsDashboardApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.communications.views', 'ListView')
    update_view = get_class('dashboard.communications.views', 'UpdateView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='comms-list'),
            url(r'^(?P<slug>\w+)/$', self.update_view.as_view(),
                name='comms-update'),
        ]
        return self.post_process_urls(urls)


application = CommsDashboardApplication()
