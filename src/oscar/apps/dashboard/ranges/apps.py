from django.urls import path
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
            path('', self.list_view.as_view(), name='range-list'),
            path('create/', self.create_view.as_view(), name='range-create'),
            path('<int:pk>/', self.update_view.as_view(), name='range-update'),
            path('<int:pk>/delete/', self.delete_view.as_view(), name='range-delete'),
            path('<int:pk>/products/', self.products_view.as_view(), name='range-products'),
            path('<int:pk>/reorder/', self.reorder_view.as_view(), name='range-reorder'),
        ]
        return self.post_process_urls(urlpatterns)
