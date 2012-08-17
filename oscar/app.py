from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth import views as auth_views

from oscar.core.application import Application
from oscar.apps.catalogue.app import application as catalogue_app
from oscar.apps.customer.app import application as customer_app
from oscar.apps.basket.app import application as basket_app
from oscar.apps.checkout.app import application as checkout_app
from oscar.apps.promotions.app import application as promotions_app
from oscar.apps.search.app import application as search_app
from oscar.apps.offer.app import application as offer_app
from oscar.apps.dashboard.app import application as dashboard_app


class Shop(Application):
    name = None

    catalogue_app = catalogue_app
    customer_app = customer_app
    basket_app = basket_app
    checkout_app = checkout_app
    promotions_app = promotions_app
    search_app = search_app
    dashboard_app = dashboard_app
    offer_app = offer_app

    def get_urls(self):
        urlpatterns = patterns('',
            (r'^products/', include(self.catalogue_app.urls)),
            (r'^basket/', include(self.basket_app.urls)),
            (r'^checkout/', include(self.checkout_app.urls)),
            (r'^accounts/', include(self.customer_app.urls)),
            (r'^search/', include(self.search_app.urls)),
            (r'^dashboard/', include(self.dashboard_app.urls)),
            (r'^offers/', include(self.offer_app.urls)),

            # Password reset - as we're using Django's default view funtions, we
            # can't namespace these urls as that prevents the reverse function
            # from working.
            url(r'^password-reset/$', auth_views.password_reset, name='password-reset'),
            url(r'^password-reset/done/$', auth_views.password_reset_done, name='password-reset-done'),
            url(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                auth_views.password_reset_confirm, name='password-reset-confirm'),
            url(r'^password-reset/complete/$', auth_views.password_reset_complete, name='password-reset-complete'),

            (r'', include(self.promotions_app.urls)),
        )
        return urlpatterns


# 'shop' kept for legacy projects - 'application' is a better name
shop = application = Shop()