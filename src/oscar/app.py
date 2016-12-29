# flake8: noqa, because URL syntax is more readable with long lines

from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse_lazy

from oscar.core.application import Application
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

    password_reset_form = get_class('customer.forms', 'PasswordResetForm')
    set_password_form = get_class('customer.forms', 'SetPasswordForm')

    def get_urls(self):
        urls = [
            url(r'^catalogue/', include(self.catalogue_app.urls)),
            url(r'^basket/', include(self.basket_app.urls)),
            url(r'^checkout/', include(self.checkout_app.urls)),
            url(r'^accounts/', include(self.customer_app.urls)),
            url(r'^search/', include(self.search_app.urls)),
            url(r'^dashboard/', include(self.dashboard_app.urls)),
            url(r'^offers/', include(self.offer_app.urls)),

            # Password reset - as we're using Django's default view functions,
            # we can't namespace these urls as that prevents
            # the reverse function from working.
            url(r'^password-reset/$',
                login_forbidden(auth_views.password_reset),
                {'password_reset_form': self.password_reset_form,
                 'post_reset_redirect': reverse_lazy('password-reset-done')},
                name='password-reset'),
            url(r'^password-reset/done/$',
                login_forbidden(auth_views.password_reset_done),
                name='password-reset-done'),
            url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                login_forbidden(auth_views.password_reset_confirm),
                {
                    'post_reset_redirect': reverse_lazy('password-reset-complete'),
                    'set_password_form': self.set_password_form,
                },
                name='password-reset-confirm'),
            url(r'^password-reset/complete/$',
                login_forbidden(auth_views.password_reset_complete),
                name='password-reset-complete'),
        ]

        if settings.OSCAR_PROMOTIONS_ENABLED:
            urls.append(url(r'', include(self.promotions_app.urls)))
        return urls

application = Shop()
