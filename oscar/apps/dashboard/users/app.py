from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.users import views
from oscar.apps.dashboard.nav import register, Node

node = Node('Customers')
node.add_child(Node('Customers', 'dashboard:users-index'))
node.add_child(Node('Notifications', 'dashboard:user-notification-list'))
register(node, 30)


class UserManagementApplication(Application):
    name = None
    index_view = views.IndexView
    user_detail_view = views.UserDetailView
    notification_list_view = views.NotificationListView
    notification_update_view = views.NotificationUpdateView
    notification_delete_view = views.NotificationDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='users-index'),
            url(r'^notification/(?P<pk>\d+)/delete/$',
                self.notification_delete_view.as_view(),
                name='user-notification-delete'),
            url(r'^notification/(?P<pk>\d+)/update/$',
                self.notification_update_view.as_view(),
                name='user-notification-update'),
            url(r'^notifications/$',
                self.notification_list_view.as_view(),
                name='user-notification-list'),
            url(r'^(?P<pk>[-\w]+)/$',
                self.user_detail_view.as_view(), name='user-detail'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = UserManagementApplication()
