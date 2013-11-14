from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.communications import views


class CommsDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    list_view = views.ListView
    update_view = views.UpdateView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='comms-list'),
            url(r'^(?P<code>\w+)/$', self.update_view.as_view(),
                name='comms-update'),
        )
        return self.post_process_urls(urlpatterns)


application = CommsDashboardApplication()
