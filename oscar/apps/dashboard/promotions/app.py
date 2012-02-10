from django.conf.urls.defaults import patterns, url
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.promotions import views


class PromotionsDashboardApplication(Application):
    name = None
    list_view = views.ListView
    page_list = views.PageListView
    create_redirect_view = views.CreateRedirectView

    create_rawhtml_view = views.CreateRawHTMLView
    update_rawhtml_view = views.UpdateRawHTMLView
    delete_rawhtml_view = views.DeleteRawHTMLView

    create_singleproduct_view = views.CreateSingleProductView
    update_singleproduct_view = views.UpdateSingleProductView
    delete_singleproduct_view = views.DeleteSingleProductView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='promotion-list'),
            url(r'^pages/$', self.page_list.as_view(), name='promotion-list-by-page'),
            url(r'^create/$', 
                self.create_redirect_view.as_view(), 
                name='promotion-create-redirect'),
            # Raw HTML
            url(r'^create/rawhtml/$',
                self.create_rawhtml_view.as_view(),
                name='promotion-create-rawhtml'),
            url(r'^update/(?P<ptype>rawhtml)/(?P<pk>\d+)/$',
                self.update_rawhtml_view.as_view(),
                name='promotion-update'),
            url(r'^delete/(?P<ptype>rawhtml)/(?P<pk>\d+)/$',
                self.delete_rawhtml_view.as_view(),
                name='promotion-delete'),
            # Single product
            url(r'^create/singleproduct/$',
                self.create_singleproduct_view.as_view(),
                name='promotion-create-singleproduct'),
            url(r'^update/(?P<ptype>singleproduct)/(?P<pk>\d+)/$',
                self.update_singleproduct_view.as_view(),
                name='promotion-update'),
            url(r'^delete/(?P<ptype>singleproduct)/(?P<pk>\d+)/$',
                self.delete_singleproduct_view.as_view(),
                name='promotion-delete'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PromotionsDashboardApplication()
