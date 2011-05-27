from oscar.core.application import Application
from django.conf.urls.defaults import patterns, url, include
from oscar.apps.product.reviews.views import ProductReviewDetailView, CreateProductReviewView, CreateReviewCompleteView, ProductReviewListView 

class ProductReviewsApplication(Application):
    name = None
    detail_view = ProductReviewDetailView
    create_view = CreateProductReviewView
    create_complete_view = CreateReviewCompleteView
    list_view = ProductReviewListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^(?P<pk>\d+)/$', self.detail_view.as_view(), name='reviews-detail'),
            url(r'^add/$', self.create_view.as_view(), name='reviews-add'),
            url(r'^add/complete/$', self.create_complete_view.as_view(), name='reviews-add-complete'),            
            url(r'^$', self.list_view.as_view(), name='reviews-list'),
        )
        return urlpatterns

application = ProductReviewsApplication()