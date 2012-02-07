from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.promotions import views


class PromotionsDashboardApplication(Application):
    name = None
    promotion_list_view = views.PromotionListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.promotion_list_view.as_view(), name='promotion-list'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PromotionsDashboardApplication()
