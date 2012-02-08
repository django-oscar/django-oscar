from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.promotions import views


class PromotionsDashboardApplication(Application):
    name = None
    promotion_list_view = views.PromotionListView
    promotion_create_redirect_view = views.PromotionCreateRedirectView
    promotion_create_rawhtml_view = views.PromotionCreateRawHTMLView
    promotion_update_rawhtml_view = views.PromotionUpdateRawHTMLView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.promotion_list_view.as_view(), name='promotion-list'),
            url(r'^create/$', 
                self.promotion_create_redirect_view.as_view(), 
                name='promotion-create-redirect'),
            url(r'^create/rawhtml/$',
                self.promotion_create_rawhtml_view.as_view(),
                name='promotion-create-rawhtml'),
            url(r'^update/(?P<ptype>rawhtml)/(?P<pk>\d+)/$',
                self.promotion_update_rawhtml_view.as_view(),
                name='promotion-update'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PromotionsDashboardApplication()
