from django.conf.urls import url, include

from oscar.core.application import Application
from oscar.core.loading import get_class


class DashboardApplication(Application):
    name = 'dashboard'
    permissions_map = {
        'index': (['is_staff'], ['partner.dashboard_access']),
    }

    index_view = get_class('dashboard.views', 'IndexView')
    orders_app = get_class('dashboard.orders.app', 'application')
    users_app = get_class('dashboard.users.app', 'application')
    catalogue_app = get_class('dashboard.catalogue.app', 'application')
    partners_app = get_class('dashboard.partners.app', 'application')
    offers_app = get_class('dashboard.offers.app', 'application')
    ranges_app = get_class('dashboard.ranges.app', 'application')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^catalogue/', include(self.catalogue_app.urls)),
            url(r'^orders/', include(self.orders_app.urls)),
            url(r'^users/', include(self.users_app.urls)),
            url(r'^partners/', include(self.partners_app.urls)),
            url(r'^offers/', include(self.offers_app.urls)),
            url(r'^ranges/', include(self.ranges_app.urls)),
        ]
        return self.post_process_urls(urls)


application = DashboardApplication()
