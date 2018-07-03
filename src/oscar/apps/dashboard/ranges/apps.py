from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class RangesDashboardConfig(OscarDashboardConfig):
    label = 'ranges_dashboard'
    name = 'oscar.apps.dashboard.ranges'
    verbose_name = _('Ranges dashboard')

    default_permissions = ['is_staff', ]

    def ready(self):
        self.list_view = get_class('dashboard.ranges.views', 'RangeListView')
        self.create_view = get_class('dashboard.ranges.views', 'RangeCreateView')
        self.update_view = get_class('dashboard.ranges.views', 'RangeUpdateView')
        self.delete_view = get_class('dashboard.ranges.views', 'RangeDeleteView')
        self.products_view = get_class('dashboard.ranges.views', 'RangeProductListView')
        self.reorder_view = get_class('dashboard.ranges.views', 'RangeReorderView')

    def get_urls(self):
        urlpatterns = [
            url(r'^$', self.list_view.as_view(), name='range-list'),
            url(r'^create/$', self.create_view.as_view(), name='range-create'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(),
                name='range-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='range-delete'),
            url(r'^(?P<pk>\d+)/products/$', self.products_view.as_view(),
                name='range-products'),
            url(r'^(?P<pk>\d+)/reorder/$', self.reorder_view.as_view(),
                name='range-reorder'),
        ]
        return self.post_process_urls(urlpatterns)
