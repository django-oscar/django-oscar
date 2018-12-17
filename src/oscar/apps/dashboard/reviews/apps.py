from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ReviewsDashboardConfig(OscarDashboardConfig):
    label = 'reviews_dashboard'
    name = 'oscar.apps.dashboard.reviews'
    verbose_name = _('Reviews dashboard')

    default_permissions = ['is_staff', ]

    def ready(self):
        self.list_view = get_class('dashboard.reviews.views', 'ReviewListView')
        self.update_view = get_class('dashboard.reviews.views', 'ReviewUpdateView')
        self.delete_view = get_class('dashboard.reviews.views', 'ReviewDeleteView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(),
                name='reviews-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='reviews-delete'),
        ]
        return self.post_process_urls(urls)
