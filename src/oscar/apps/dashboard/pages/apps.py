from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PagesDashboardConfig(OscarDashboardConfig):
    label = 'pages_dashboard'
    name = 'oscar.apps.dashboard.pages'
    verbose_name = _('Pages dashboard')

    default_permissions = ['is_staff', ]

    def ready(self):
        self.list_view = get_class('dashboard.pages.views', 'PageListView')
        self.create_view = get_class('dashboard.pages.views', 'PageCreateView')
        self.update_view = get_class('dashboard.pages.views', 'PageUpdateView')
        self.delete_view = get_class('dashboard.pages.views', 'PageDeleteView')

    def get_urls(self):
        """
        Get URL patterns defined for flatpage management application.
        """
        urls = [
            url(r'^$', self.list_view.as_view(), name='page-list'),
            url(r'^create/$', self.create_view.as_view(), name='page-create'),
            url(r'^update/(?P<pk>[-\w]+)/$',
                self.update_view.as_view(), name='page-update'),
            url(r'^delete/(?P<pk>\d+)/$',
                self.delete_view.as_view(), name='page-delete')
        ]
        return self.post_process_urls(urls)
