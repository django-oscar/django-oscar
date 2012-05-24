from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.reports import views
from oscar.apps.dashboard.nav import register, Node

node = Node('Reports', 'dashboard:reports-index')
register(node, 90)


class ReportsApplication(Application):
    name = None
    index_view = views.IndexView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='reports-index'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = ReportsApplication()
