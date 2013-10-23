from django.conf.urls import patterns, url, include
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse_lazy

from oscar.core.application import Application

from oscar.apps.customer import forms
from oscar.core.loading import get_class
from oscar.views.decorators import login_forbidden


class Shop(Application):
    name = None

    catalogue_app = get_class('catalogue.app', 'application')
    customer_app = get_class('customer.app', 'application')
    basket_app = get_class('basket.app', 'application')
    checkout_app = get_class('checkout.app', 'application')
    promotions_app = get_class('promotions.app', 'application')
    search_app = get_class('search.app', 'application')
    dashboard_app = get_class('dashboard.app', 'application')
    offer_app = get_class('offer.app', 'application')

    def get_urls(self):
        urlpatterns = patterns('',
            (r'^i18n/', include('django.conf.urls.i18n')),
            (r'^catalogue/', include(self.catalogue_app.urls)),
            (r'^basket/', include(self.basket_app.urls)),
            (r'^checkout/', include(self.checkout_app.urls)),
            (r'^accounts/', include(self.customer_app.urls)),
            (r'^search/', include(self.search_app.urls)),
            (r'^dashboard/', include(self.dashboard_app.urls)),
            (r'^offers/', include(self.offer_app.urls)),

            # Password reset - as we're using Django's default view funtions,
            # we can't namespace these urls as that prevents
            # the reverse function from working.
            url(r'^password-reset/$',
                login_forbidden(auth_views.password_reset),
                {'password_reset_form': forms.PasswordResetForm,
                 'post_reset_redirect': reverse_lazy('password-reset-done')},
                name='password-reset'),
            url(r'^password-reset/done/$',
                login_forbidden(auth_views.password_reset_done),
                name='password-reset-done'),
            url(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                login_forbidden(auth_views.password_reset_confirm),
                {'post_reset_redirect': reverse_lazy('password-reset-complete')},
                name='password-reset-confirm'),
            url(r'^password-reset/complete/$',
                login_forbidden(auth_views.password_reset_complete),
                name='password-reset-complete'),
            (r'', include(self.promotions_app.urls)),
        )
        return urlpatterns


# 'shop' kept for legacy projects - 'application' is a better name
shop = application = Shop()
