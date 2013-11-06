from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.ranges import views


class RangeDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    list_view = views.RangeListView
    create_view = views.RangeCreateView
    update_view = views.RangeUpdateView
    delete_view = views.RangeDeleteView
    products_view = views.RangeProductListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='range-list'),
            url(r'^create/$', self.create_view.as_view(), name='range-create'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(), name='range-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(), name='range-delete'),
            url(r'^(?P<pk>\d+)/products/$', self.products_view.as_view(), name='range-products'),
        )
        return self.post_process_urls(urlpatterns)


application = RangeDashboardApplication()
