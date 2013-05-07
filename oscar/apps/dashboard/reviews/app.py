from django.conf.urls import patterns, url

from oscar.views.decorators import staff_member_required
from oscar.core.application import Application
from oscar.apps.dashboard.reviews import views


class ReviewsApplication(Application):
    name = None
    list_view = views.ReviewListView
    update_view = views.ReviewUpdateView
    delete_view = views.ReviewDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
            url(r'^(?P<pk>\d+)/$', self.update_view.as_view(),
                name='reviews-update'
            ),
            url(r'^(?P<pk>\d+)/delete/$', self.delete_view.as_view(),
                name='reviews-delete'
            ),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = ReviewsApplication()
