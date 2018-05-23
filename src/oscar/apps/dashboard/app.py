from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm

from oscar.core.application import (
    DashboardApplication as BaseDashboardApplication)
from oscar.core.loading import get_class


class DashboardApplication(BaseDashboardApplication):
    name = 'dashboard'
    permissions_map = {
        'index': (['is_staff'], ['partner.dashboard_access']),
    }

    index_view = get_class('dashboard.views', 'IndexView')
    reports_app = get_class('dashboard.reports.app', 'application')
    orders_app = get_class('dashboard.orders.app', 'application')
    users_app = get_class('dashboard.users.app', 'application')
    catalogue_app = get_class('dashboard.catalogue.app', 'application')
    promotions_app = get_class('dashboard.promotions.app', 'application')
    pages_app = get_class('dashboard.pages.app', 'application')
    partners_app = get_class('dashboard.partners.app', 'application')
    offers_app = get_class('dashboard.offers.app', 'application')
    ranges_app = get_class('dashboard.ranges.app', 'application')
    reviews_app = get_class('dashboard.reviews.app', 'application')
    vouchers_app = get_class('dashboard.vouchers.app', 'application')
    comms_app = get_class('dashboard.communications.app', 'application')
    shipping_app = get_class('dashboard.shipping.app', 'application')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^catalogue/', self.catalogue_app.urls),
            url(r'^reports/', self.reports_app.urls),
            url(r'^orders/', self.orders_app.urls),
            url(r'^users/', self.users_app.urls),
            url(r'^content-blocks/', self.promotions_app.urls),
            url(r'^pages/', self.pages_app.urls),
            url(r'^partners/', self.partners_app.urls),
            url(r'^offers/', self.offers_app.urls),
            url(r'^ranges/', self.ranges_app.urls),
            url(r'^reviews/', self.reviews_app.urls),
            url(r'^vouchers/', self.vouchers_app.urls),
            url(r'^comms/', self.comms_app.urls),
            url(r'^shipping/', self.shipping_app.urls),

            url(r'^login/$',
                auth_views.LoginView.as_view(template_name='dashboard/login.html',
                                             authentication_form=AuthenticationForm),
                name='login'),
            url(r'^logout/$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

        ]
        return self.post_process_urls(urls)


application = DashboardApplication()
