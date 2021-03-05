# flake8: noqa, because URL syntax is more readable with long lines

from django.conf import settings
from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class Shop(OscarConfig):
    name = 'oscar'

    def get_app_label_and_url_endpoint_mappings(self):
        return {
            'catalogue': 'catalogue/',
            'customer': 'accounts/',
            'basket': 'basket/',
            'checkout': 'checkout/',
            'search': 'search/',
            'dashboard': 'dashboard/',
            'offer': 'offers/',
        }

    def ready(self):
        super().ready()
        from django.contrib.auth.forms import SetPasswordForm

        self.password_reset_form = get_class('customer.forms', 'PasswordResetForm')
        self.set_password_form = SetPasswordForm

    def get_urls(self):
        from django.contrib.auth import views as auth_views

        from oscar.views.decorators import login_forbidden

        auto_loaded_urls = self.get_auto_loaded_urls()

        urls = [path('', RedirectView.as_view(url=settings.OSCAR_HOMEPAGE), name='home')] + auto_loaded_urls + [

            # Password reset - as we're using Django's default view functions,
            # we can't namespace these urls as that prevents
            # the reverse function from working.
            path('password-reset/',
                login_forbidden(
                    auth_views.PasswordResetView.as_view(
                        form_class=self.password_reset_form,
                        success_url=reverse_lazy('password-reset-done'),
                        template_name='oscar/registration/password_reset_form.html'
                    )
                ),
                name='password-reset'),
            path('password-reset/done/',
                login_forbidden(auth_views.PasswordResetDoneView.as_view(
                    template_name='oscar/registration/password_reset_done.html'
                )),
                name='password-reset-done'),
            path('password-reset/confirm/<str:uidb64>/<str:token>/',
                login_forbidden(
                    auth_views.PasswordResetConfirmView.as_view(
                        form_class=self.set_password_form,
                        success_url=reverse_lazy('password-reset-complete'),
                        template_name='oscar/registration/password_reset_confirm.html'
                    )
                ),
                name='password-reset-confirm'),
            path('password-reset/complete/',
                login_forbidden(auth_views.PasswordResetCompleteView.as_view(
                    template_name='oscar/registration/password_reset_complete.html'
                )),
                name='password-reset-complete'),
        ]
        return urls
