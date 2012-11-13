from django.conf.urls import patterns, url, include
from oscar.views.decorators import staff_member_required

from oscar.core.application import Application
from oscar.apps.dashboard.reports.app import application as reports_app
from oscar.apps.dashboard.orders.app import application as orders_app
from oscar.apps.dashboard.users.app import application as users_app
from oscar.apps.dashboard.promotions.app import application as promotions_app
from oscar.apps.dashboard.catalogue.app import application as catalogue_app
from oscar.apps.dashboard.pages.app import application as pages_app
from oscar.apps.dashboard.offers.app import application as offers_app
from oscar.apps.dashboard.ranges.app import application as ranges_app
from oscar.apps.dashboard.reviews.app import application as reviews_app
from oscar.apps.dashboard.vouchers.app import application as vouchers_app
from oscar.apps.dashboard.communications.app import application as comms_app
from oscar.apps.dashboard import views


class DashboardApplication(Application):
    name = 'dashboard'

    index_view = views.IndexView
    reports_app = reports_app
    orders_app = orders_app
    users_app = users_app
    catalogue_app = catalogue_app
    promotions_app = promotions_app
    pages_app = pages_app
    offers_app = offers_app
    ranges_app = ranges_app
    reviews_app = reviews_app
    vouchers_app = vouchers_app
    comms_app = comms_app

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^catalogue/', include(self.catalogue_app.urls)),
            url(r'^reports/', include(self.reports_app.urls)),
            url(r'^orders/', include(self.orders_app.urls)),
            url(r'^users/', include(self.users_app.urls)),
            url(r'^content-blocks/', include(self.promotions_app.urls)),
            url(r'^pages/', include(self.pages_app.urls)),
            url(r'^offers/', include(self.offers_app.urls)),
            url(r'^ranges/', include(self.ranges_app.urls)),
            url(r'^reviews/', include(self.reviews_app.urls)),
            url(r'^vouchers/', include(self.vouchers_app.urls)),
            url(r'^comms/', include(self.comms_app.urls)),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = DashboardApplication()
