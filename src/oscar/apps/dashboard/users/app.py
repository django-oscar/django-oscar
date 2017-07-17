from django.conf.urls import url

from oscar.core.application import Application
from oscar.core.loading import get_class


class UserManagementApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    index_view = get_class('dashboard.users.views', 'IndexView')
    user_detail_view = get_class('dashboard.users.views', 'UserDetailView')
    password_reset_view = get_class('dashboard.users.views',
                                    'PasswordResetView')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='users-index'),
            url(r'^(?P<pk>-?\d+)/$',
                self.user_detail_view.as_view(), name='user-detail'),
            url(r'^(?P<pk>-?\d+)/password-reset/$',
                self.password_reset_view.as_view(),
                name='user-password-reset'),
        ]
        return self.post_process_urls(urls)


application = UserManagementApplication()
