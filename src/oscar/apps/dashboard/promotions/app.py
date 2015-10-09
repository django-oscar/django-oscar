from django.conf.urls import url

from oscar.apps.promotions.conf import PROMOTION_CLASSES
from oscar.core.application import Application
from oscar.core.loading import get_class


class PromotionsDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff', ]

    list_view = get_class('dashboard.promotions.views',
                          'ListView')
    page_list = get_class('dashboard.promotions.views',
                          'PageListView')
    page_detail = get_class('dashboard.promotions.views',
                            'PageDetailView')
    create_redirect_view = get_class('dashboard.promotions.views',
                                     'CreateRedirectView')
    delete_page_promotion_view = get_class('dashboard.promotions.views',
                                           'DeletePagePromotionView')

    # Dynamically set the CRUD views for all promotion classes
    view_names = (
        ('create_%s_view', 'Create%sView'),
        ('update_%s_view', 'Update%sView'),
        ('delete_%s_view', 'Delete%sView')
    )
    for klass in PROMOTION_CLASSES:
        for attr_name, view_name in view_names:
            full_attr_name = attr_name % klass.classname()
            full_view_name = view_name % klass.__name__
            view = get_class('dashboard.promotions.views', full_view_name)
            locals()[full_attr_name] = view

    def get_urls(self):
        urls = [
            url(r'^$', self.list_view.as_view(), name='promotion-list'),
            url(r'^pages/$', self.page_list.as_view(),
                name='promotion-list-by-page'),
            url(r'^page/(?P<path>/([\w-]+(/[\w-]+)*/)?)$',
                self.page_detail.as_view(), name='promotion-list-by-url'),
            url(r'^create/$',
                self.create_redirect_view.as_view(),
                name='promotion-create-redirect'),
            url(r'^page-promotion/(?P<pk>\d+)/$',
                self.delete_page_promotion_view.as_view(),
                name='pagepromotion-delete')]

        for klass in PROMOTION_CLASSES:
            code = klass.classname()
            urls += [
                url(r'create/%s/' % code,
                    getattr(self, 'create_%s_view' % code).as_view(),
                    name='promotion-create-%s' % code),
                url(r'^update/(?P<ptype>%s)/(?P<pk>\d+)/$' % code,
                    getattr(self, 'update_%s_view' % code).as_view(),
                    name='promotion-update'),
                url(r'^delete/(?P<ptype>%s)/(?P<pk>\d+)/$' % code,
                    getattr(self, 'delete_%s_view' % code).as_view(),
                    name='promotion-delete')]

        return self.post_process_urls(urls)


application = PromotionsDashboardApplication()
