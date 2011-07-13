from oscar.core.application import Application
from django.conf.urls.defaults import patterns, url, include
from oscar.apps.catalogue.reviews.views import ProductReviewDetail, CreateProductReview, CreateProductReviewComplete, ProductReviewList 

class ProductReviewsApplication(Application):
    name = None
    detail_view = ProductReviewDetail
    create_view = CreateProductReview
    create_complete_view = CreateProductReviewComplete
    list_view = ProductReviewList

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(), name='reviews-detail'),
            url(r'^add/$', self.create_view.as_view(), name='reviews-add'),
            url(r'^add/complete/$', self.create_complete_view.as_view(), name='reviews-add-complete'),            
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
        )
        return urlpatterns

application = ProductReviewsApplication()