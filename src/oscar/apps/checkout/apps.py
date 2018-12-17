from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CheckoutConfig(OscarConfig):
    label = 'checkout'
    name = 'oscar.apps.checkout'
    verbose_name = _('Checkout')

    namespace = 'checkout'

    def ready(self):
        self.index_view = get_class('checkout.views', 'IndexView')
        self.shipping_address_view = get_class('checkout.views', 'ShippingAddressView')
        self.user_address_update_view = get_class('checkout.views',
                                                  'UserAddressUpdateView')
        self.user_address_delete_view = get_class('checkout.views',
                                                  'UserAddressDeleteView')
        self.shipping_method_view = get_class('checkout.views', 'ShippingMethodView')
        self.payment_method_view = get_class('checkout.views', 'PaymentMethodView')
        self.payment_details_view = get_class('checkout.views', 'PaymentDetailsView')
        self.thankyou_view = get_class('checkout.views', 'ThankYouView')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),

            # Shipping/user address views
            url(r'shipping-address/$',
                self.shipping_address_view.as_view(), name='shipping-address'),
            url(r'user-address/edit/(?P<pk>\d+)/$',
                self.user_address_update_view.as_view(),
                name='user-address-update'),
            url(r'user-address/delete/(?P<pk>\d+)/$',
                self.user_address_delete_view.as_view(),
                name='user-address-delete'),

            # Shipping method views
            url(r'shipping-method/$',
                self.shipping_method_view.as_view(), name='shipping-method'),

            # Payment views
            url(r'payment-method/$',
                self.payment_method_view.as_view(), name='payment-method'),
            url(r'payment-details/$',
                self.payment_details_view.as_view(), name='payment-details'),

            # Preview and thankyou
            url(r'preview/$',
                self.payment_details_view.as_view(preview=True),
                name='preview'),
            url(r'thank-you/$', self.thankyou_view.as_view(),
                name='thank-you'),
        ]
        return self.post_process_urls(urls)

    def get_url_decorator(self, pattern):
        if not settings.OSCAR_ALLOW_ANON_CHECKOUT:
            return login_required
        if pattern.name.startswith('user-address'):
            return login_required
        return None
