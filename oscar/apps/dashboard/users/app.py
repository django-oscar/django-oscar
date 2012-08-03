from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.users import views
from oscar.apps.dashboard.nav import register, Node

node = Node(_('Customers'))
node.add_child(Node(_('Customers'), 'dashboard:users-index'))
node.add_child(Node(_('Notifications'), 'dashboard:user-notification-list'))
register(node, 30)


class UserManagementApplication(Application):
    name = None
    index_view = views.IndexView
    user_detail_view = views.UserDetailView
    notification_list_view = views.ProductNotificationListView
    notification_update_view = views.ProductNotificationUpdateView
    notification_delete_view = views.ProductNotificationDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='users-index'),
            url(r'^notifications/(?P<pk>\d+)/delete/$',
                self.notification_delete_view.as_view(),
                name='user-notification-delete'),
            url(r'^notifications/(?P<pk>\d+)/update/$',
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
