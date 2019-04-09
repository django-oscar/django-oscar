from django.apps import apps
from django.conf.urls import include, url
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class DashboardConfig(OscarDashboardConfig):
    label = 'dashboard'
    name = 'oscar.apps.dashboard'
    verbose_name = _('Dashboard')

    namespace = 'dashboard'
    permissions_map = {
        'index': (['is_staff'], ['partner.dashboard_access']),
    }

    def ready(self):
        self.index_view = get_class('dashboard.views', 'IndexView')

        self.catalogue_app = apps.get_app_config('catalogue_dashboard')
        self.reports_app = apps.get_app_config('reports_dashboard')
        self.orders_app = apps.get_app_config('orders_dashboard')
        self.users_app = apps.get_app_config('users_dashboard')
        self.pages_app = apps.get_app_config('pages_dashboard')
        self.partners_app = apps.get_app_config('partners_dashboard')
        self.offers_app = apps.get_app_config('offers_dashboard')
        self.ranges_app = apps.get_app_config('ranges_dashboard')
        self.reviews_app = apps.get_app_config('reviews_dashboard')
        self.vouchers_app = apps.get_app_config('vouchers_dashboard')
        self.comms_app = apps.get_app_config('communications_dashboard')
        self.shipping_app = apps.get_app_config('shipping_dashboard')

    def get_urls(self):
        from django.contrib.auth import views as auth_views
        from django.contrib.auth.forms import AuthenticationForm

        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^catalogue/', include(self.catalogue_app.urls[0])),
            url(r'^reports/', include(self.reports_app.urls[0])),
            url(r'^orders/', include(self.orders_app.urls[0])),
            url(r'^users/', include(self.users_app.urls[0])),
            url(r'^pages/', include(self.pages_app.urls[0])),
            url(r'^partners/', include(self.partners_app.urls[0])),
            url(r'^offers/', include(self.offers_app.urls[0])),
            url(r'^ranges/', include(self.ranges_app.urls[0])),
            url(r'^reviews/', include(self.reviews_app.urls[0])),
            url(r'^vouchers/', include(self.vouchers_app.urls[0])),
            url(r'^comms/', include(self.comms_app.urls[0])),
            url(r'^shipping/', include(self.shipping_app.urls[0])),

            url(r'^login/$',
                auth_views.LoginView.as_view(template_name='oscar/dashboard/login.html',
                                             authentication_form=AuthenticationForm),
                name='login'),
            url(r'^logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

        ]
        return self.post_process_urls(urls)
