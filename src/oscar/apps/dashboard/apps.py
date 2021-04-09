from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import (
    AutoLoadURLsConfigMixin, OscarDashboardConfig)
from oscar.core.loading import get_class


class DashboardConfig(AutoLoadURLsConfigMixin, OscarDashboardConfig):
    label = 'dashboard'
    name = 'oscar.apps.dashboard'
    verbose_name = _('Dashboard')

    namespace = 'dashboard'
    permissions_map = {
        'index': (['is_staff'], ['partner.dashboard_access']),
    }

    def get_app_label_url_endpoint_mapping(self):
        return {
            'catalogue_dashboard': 'catalogue/',
            'reports_dashboard': 'reports/',
            'orders_dashboard': 'orders/',
            'users_dashboard': 'users/',
            'pages_dashboard': 'pages/',
            'partners_dashboard': 'partners/',
            'offers_dashboard': 'offers/',
            'ranges_dashboard': 'ranges/',
            'reviews_dashboard': 'reviews/',
            'vouchers_dashboard': 'vouchers/',
            'communications_dashboard': 'comms/',
            'shipping_dashboard': 'shipping/',
        }

    def ready(self):
        super().ready()
        self.index_view = get_class('dashboard.views', 'IndexView')
        self.login_view = get_class('dashboard.views', 'LoginView')

    def get_urls(self):
        from django.contrib.auth import views as auth_views

        urls = [path('', self.index_view.as_view(), name='index')] + self.get_auto_loaded_urls() + [
            path('login/', self.login_view.as_view(), name='login'),
            path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
        ]
        return self.post_process_urls(urls)
