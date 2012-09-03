from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import Application
from oscar.apps.dashboard.catalogue import views
from oscar.apps.dashboard.nav import register, Node

node = Node(_('Catalogue'))
node.add_child(Node(_('Products'), 'dashboard:catalogue-product-list'))
node.add_child(Node(_('Categories'), 'dashboard:catalogue-category-list'))
node.add_child(Node(_('Stock alerts'), 'dashboard:stock-alert-list'))
register(node, 10)


class CatalogueApplication(Application):
    name = None

    product_list_view = views.ProductListView
    product_create_redirect_view = views.ProductCreateRedirectView
    product_create_view = views.ProductCreateView
    product_update_view = views.ProductUpdateView
    
    category_list_view = views.CategoryListView
    category_detail_list_view = views.CategoryDetailListView
    category_create_view = views.CategoryCreateView
    category_update_view = views.CategoryUpdateView
    category_delete_view = views.CategoryDeleteView

    stock_alert_view = views.StockAlertListView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^products/(?P<pk>\d+)/$', self.product_update_view.as_view(),
                name='catalogue-product'),
            url(r'^products/create/$', self.product_create_redirect_view.as_view(),
                name='catalogue-product-create'),
            url(r'^products/create/(?P<product_class_id>\d+)/$', self.product_create_view.as_view(),
                name='catalogue-product-create'),
            url(r'^$', self.product_list_view.as_view(),
                name='catalogue-product-list'),
            url(r'^stock-alerts/$', self.stock_alert_view.as_view(),
                name='stock-alert-list'),
            url(r'^categories/$', self.category_list_view.as_view(),
                name='catalogue-category-list'),
            url(r'^categories/(?P<pk>\d+)/$', self.category_detail_list_view.as_view(),
                name='catalogue-category-detail-list'),
            url(r'^categories/create/$', self.category_create_view.as_view(),
                name='catalogue-category-create'),
            url(r'^categories/update/(?P<pk>\d+)/$', self.category_update_view.as_view(),
                name='catalogue-category-update'),
            url(r'^categories/delete/(?P<pk>\d+)/$', self.category_delete_view.as_view(),
                name='catalogue-category-delete'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = CatalogueApplication()
