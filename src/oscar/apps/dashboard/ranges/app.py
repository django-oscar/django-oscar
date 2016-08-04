from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class RangeDashboardApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.ranges.views', 'RangeListView')
    create_view = get_class('dashboard.ranges.views', 'RangeCreateView')
    update_view = get_class('dashboard.ranges.views', 'RangeUpdateView')
    delete_view = get_class('dashboard.ranges.views', 'RangeDeleteView')
    products_view = get_class('dashboard.ranges.views', 'RangeProductListView')
    reorder_view = get_class('dashboard.ranges.views', 'RangeReorderView')

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


application = RangeDashboardApplication()
