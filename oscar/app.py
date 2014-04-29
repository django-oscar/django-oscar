# flake8: noqa, because URL syntax is more readable with long lines

import django
from django.conf.urls import url, include
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
                {'password_reset_form': forms.PasswordResetForm,
                 'post_reset_redirect': reverse_lazy('password-reset-done')},
                name='password-reset'),
            url(r'^password-reset/done/$',
                login_forbidden(auth_views.password_reset_done),
                name='password-reset-done')]

        # Django <=1.5: uses uidb36 to encode the user's primary key
        # Django 1.6:   uses uidb64 to encode the user's primary key, but
        #               but supports legacy links
        # Django > 1.7: used uidb64 to encode the user's primary key
        # see https://docs.djangoproject.com/en/dev/releases/1.6/#django-contrib-auth-password-reset-uses-base-64-encoding-of-user-pk
        if django.VERSION < (1, 6):
            urls.append(
                url(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                    login_forbidden(auth_views.password_reset_confirm),
                    {
                        'post_reset_redirect': reverse_lazy('password-reset-complete'),
                        'set_password_form': forms.SetPasswordForm,
                    },
                    name='password-reset-confirm'))
        else:
            urls.append(
                url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                    login_forbidden(auth_views.password_reset_confirm),
                    {
                        'post_reset_redirect': reverse_lazy('password-reset-complete'),
                        'set_password_form': forms.SetPasswordForm,
                    },
                    name='password-reset-confirm'))
            if django.VERSION < (1, 7):
                urls.append(
                    url(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                        login_forbidden(auth_views.password_reset_confirm_uidb36),
                        {
                            'post_reset_redirect': reverse_lazy('password-reset-complete'),
                            'set_password_form': forms.SetPasswordForm,
                        }))

        urls += [
            url(r'^password-reset/complete/$',
                login_forbidden(auth_views.password_reset_complete),
                name='password-reset-complete'),
            url(r'', include(self.promotions_app.urls)),
        ]
        return urls


# 'shop' kept for legacy projects - 'application' is a better name
shop = application = Shop()
