from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.pages import views
from oscar.apps.dashboard.nav import register, Node

node = Node('Pages', 'dashboard:pages-index')
register(node)


class FlatPageManagementApplication(Application):
    name = None
    index_view = views.IndexView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='pages-index'),
            ##TODO setup user details
            #url(r'^(?P<pk>[-\w]+)/$',
            #    self.user_detail_view.as_view(), name='user-detail'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = FlatPageManagementApplication()
