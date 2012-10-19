from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.communications import views
from oscar.apps.dashboard.nav import register, Node

node = Node(_('Communications'))
node.add_child(Node(_('Emails'), 'dashboard:comms-list'))
register(node, 35)


class CommsDashboardApplication(Application):
    name = None
    list_view = views.ListView
    update_view = views.UpdateView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='comms-list'),
            url(r'^(?P<code>\w+)/$', self.update_view.as_view(),
                name='comms-update'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = CommsDashboardApplication()
