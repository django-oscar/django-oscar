from django.conf.urls import url

from oscar.core.application import DashboardApplication
from oscar.core.loading import get_class


class ReviewsApplication(DashboardApplication):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.reviews.views', 'ReviewListView')
    update_view = get_class('dashboard.reviews.views', 'ReviewUpdateView')
    delete_view = get_class('dashboard.reviews.views', 'ReviewDeleteView')

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(),
                name='reviews-update'),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='reviews-delete'),
        ]
        return self.post_process_urls(urls)


application = ReviewsApplication()
