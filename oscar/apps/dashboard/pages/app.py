from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.pages import views
from oscar.apps.dashboard.nav import register, Node

node = Node('Pages', 'dashboard:page-list')
register(node)


class FlatPageManagementApplication(Application):
    name = None
    list_view = views.PageListView
    create_view = views.PageCreateView
    update_view = views.PageUpdateView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='page-list'),

            url(r'^create/$', self.create_view.as_view(), name='page-create'),

            url(r'^(?P<pk>[-\w]+)/$', 
                self.update_view.as_view(), name='page-update'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required

application = FlatPageManagementApplication()
