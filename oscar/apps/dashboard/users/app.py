from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.users import views


class UserManagementApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    index_view = views.IndexView
    user_detail_view = views.UserDetailView
    password_reset_view = views.PasswordResetView
    alert_list_view = views.ProductAlertListView
    alert_update_view = views.ProductAlertUpdateView
    alert_delete_view = views.ProductAlertDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='users-index'),
            url(r'^(?P<pk>\d+)/$',
                self.user_detail_view.as_view(), name='user-detail'),
            url(r'^(?P<pk>\d+)/password-reset/$',
                self.password_reset_view.as_view(),
                name='user-password-reset'),

            # Alerts
            url(r'^alerts/$',
                self.alert_list_view.as_view(),
                name='user-alert-list'),
            url(r'^alerts/(?P<pk>\d+)/delete/$',
                self.alert_delete_view.as_view(),
                name='user-alert-delete'),
            url(r'^alerts/(?P<pk>\d+)/update/$',
                self.alert_update_view.as_view(),
                name='user-alert-update'),
        )
        return self.post_process_urls(urlpatterns)


application = UserManagementApplication()
