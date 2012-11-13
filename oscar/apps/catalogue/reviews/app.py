from oscar.core.application import Application
from django.conf.urls import patterns, url
from oscar.apps.catalogue.reviews import views


class ProductReviewsApplication(Application):
    name = None
    detail_view = views.ProductReviewDetail
    create_view = views.CreateProductReview
    create_complete_view = views.CreateProductReviewComplete
    list_view = views.ProductReviewList

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(),
                name='reviews-detail'),
            url(r'^add/$', self.create_view.as_view(), name='reviews-add'),
            url(r'^add/complete/$', self.create_complete_view.as_view(),
                name='reviews-add-complete'),
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
        )
        return urlpatterns


application = ProductReviewsApplication()
