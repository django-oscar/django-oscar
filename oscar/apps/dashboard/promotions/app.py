from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.promotions import views
from oscar.apps.promotions.conf import PROMOTION_CLASSES
from oscar.apps.dashboard.nav import register, Node

node = Node(_('Content'))
node.add_child(Node(_('Re-usable content blocks'), 'dashboard:promotion-list'))
node.add_child(Node(_('Content blocks by page'), 'dashboard:promotion-list-by-page'))
node.add_child(Node(_('Pages'), 'dashboard:page-list'))
register(node, 20)


class PromotionsDashboardApplication(Application):
    name = None
    list_view = views.ListView
    page_list = views.PageListView
    page_detail = views.PageDetailView
    create_redirect_view = views.CreateRedirectView
    delete_page_promotion_view = views.DeletePagePromotionView

    for klass in PROMOTION_CLASSES:
        locals()['create_%s_view' % klass.classname()] = \
                getattr(views, 'Create%sView' % klass.__name__)
        locals()['update_%s_view' % klass.classname()] = \
                getattr(views, 'Update%sView' % klass.__name__)
        locals()['delete_%s_view' % klass.classname()] = \
                getattr(views, 'Delete%sView' % klass.__name__)

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.list_view.as_view(), name='promotion-list'),
            url(r'^pages/$', self.page_list.as_view(), name='promotion-list-by-page'),
            url(r'^pages/(?P<path>.+)/$', self.page_detail.as_view(), name='promotion-list-by-url'),
            url(r'^create/$', 
                self.create_redirect_view.as_view(), 
                name='promotion-create-redirect'),
            url(r'^page-promotion/(?P<pk>\d+)/$', 
                self.delete_page_promotion_view.as_view(), name='pagepromotion-delete')
            )

        for klass in PROMOTION_CLASSES:
            code = klass.classname()
            urlpatterns += patterns('',
                url(r'create/%s/' % code,
                    getattr(self, 'create_%s_view' % code).as_view(),
                    name='promotion-create-%s' % code),
                url(r'^update/(?P<ptype>%s)/(?P<pk>\d+)/$' % code,
                    getattr(self, 'update_%s_view' % code).as_view(),
                    name='promotion-update'),
                url(r'^delete/(?P<ptype>%s)/(?P<pk>\d+)/$' % code,
                    getattr(self, 'delete_%s_view' % code).as_view(),
                    name='promotion-delete')
            )

        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = PromotionsDashboardApplication()
