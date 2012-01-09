from django.conf.urls.defaults import patterns, url

from oscar.core.application import Application
from oscar.apps.promotions.views import HomeView, RecordClickView
from oscar.apps.promotions.models import PagePromotion, KeywordPromotion


class PromotionsApplication(Application):
    name = 'promotions'
    
    home_view = HomeView
    record_click_view = RecordClickView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'page-redirect/(?P<page_promotion_id>\d+)/$', 
                self.record_click_view.as_view(model=PagePromotion), name='page-click'),
            url(r'keyword-redirect/(?P<keyword_promotion_id>\d+)/$', 
                self.record_click_view.as_view(model=KeywordPromotion), name='keyword-click'),
            url(r'^$', self.home_view.as_view(), name='home'),
        )
        return self.post_process_urls(urlpatterns)


application = PromotionsApplication()