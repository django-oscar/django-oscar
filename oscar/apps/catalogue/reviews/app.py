from django.conf.urls import patterns, url

from oscar.core.application import Application
from . import views


class ProductReviewsApplication(Application):
    name = None
    hidable_feature_name = "reviews"

    detail_view = views.ProductReviewDetail
    create_view = views.CreateProductReview
    vote_view = views.AddVoteView
    list_view = views.ProductReviewList

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(),
                name='reviews-detail'),
            url(r'^add/$', self.create_view.as_view(), name='reviews-add'),
            url(r'^(?P<pk>\d+)/vote/$', self.vote_view.as_view(),
                name='reviews-vote'),
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
        )
        return self.post_process_urls(urlpatterns)


application = ProductReviewsApplication()
