from django.conf.urls import patterns, url

from oscar.core.application import Application
from oscar.apps.dashboard.catalogue import views


class CatalogueApplication(Application):
    name = None

    default_permissions = ['is_staff', ]
    permissions_map = _map = {
        'catalogue-product': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-create': (['is_staff'],
                                     ['partner.dashboard_access']),
        'catalogue-product-list': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-delete': (['is_staff'],
                                     ['partner.dashboard_access']),
        'catalogue-product-lookup': (['is_staff'],
                                     ['partner.dashboard_access']),
    }

    product_list_view = views.ProductListView
    product_lookup_view = views.ProductLookupView
    product_create_redirect_view = views.ProductCreateRedirectView
    product_createupdate_view = views.ProductCreateUpdateView
    product_delete_view = views.ProductDeleteView

    category_list_view = views.CategoryListView
    category_detail_list_view = views.CategoryDetailListView
    category_create_view = views.CategoryCreateView
    category_update_view = views.CategoryUpdateView
    category_delete_view = views.CategoryDeleteView

    stock_alert_view = views.StockAlertListView

    def get_urls(self):
        urls = [
            url(r'^products/(?P<pk>\d+)/$',
                self.product_createupdate_view.as_view(),
                name='catalogue-product'),
            url(r'^products/create/$',
                self.product_create_redirect_view.as_view(),
                name='catalogue-product-create'),
            url(r'^products/create/(?P<product_class_slug>[\w-]+)/$',
                self.product_createupdate_view.as_view(),
                name='catalogue-product-create'),
            url(r'^products/(?P<pk>\d+)/delete/$',
                self.product_delete_view.as_view(),
                name='catalogue-product-delete'),
            url(r'^$', self.product_list_view.as_view(),
                name='catalogue-product-list'),
            url(r'^stock-alerts/$', self.stock_alert_view.as_view(),
                name='stock-alert-list'),
            url(r'^product-lookup/$', self.product_lookup_view.as_view(),
                name='catalogue-product-lookup'),
            url(r'^categories/$', self.category_list_view.as_view(),
                name='catalogue-category-list'),
            url(r'^categories/(?P<pk>\d+)/$',
                self.category_detail_list_view.as_view(),
                name='catalogue-category-detail-list'),
            url(r'^categories/create/$', self.category_create_view.as_view(),
                name='catalogue-category-create'),
            url(r'^categories/create/(?P<parent>\d+)$',
                self.category_create_view.as_view(),
                name='catalogue-category-create-child'),
            url(r'^categories/(?P<pk>\d+)/update/$',
                self.category_update_view.as_view(),
                name='catalogue-category-update'),
            url(r'^categories/(?P<pk>\d+)/delete/$',
                self.category_delete_view.as_view(),
                name='catalogue-category-delete'),
        ]
        return self.post_process_urls(patterns('', *urls))


application = CatalogueApplication()
