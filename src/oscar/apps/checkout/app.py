from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.conf import settings

from oscar.core.application import Application
from oscar.core.loading import get_class


class CheckoutApplication(Application):
    name = 'checkout'

    index_view = get_class('checkout.views', 'IndexView')
    identify_user_view = get_class('checkout.views', 'IdentifyUserView')
    shipping_address_view = get_class('checkout.views', 'ShippingAddressView')
    user_address_update_view = get_class('checkout.views',
                                         'UserAddressUpdateView')
    user_address_delete_view = get_class('checkout.views',
                                         'UserAddressDeleteView')
    payment_details_view = get_class('checkout.views', 'PaymentDetailsView')
    thankyou_view = get_class('checkout.views', 'ThankYouView')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),

            # Identify user view
            url(r'identify-user/$',
                self.identify_user_view.as_view(), name='identify-user'),

            # Shipping/user address views
            url(r'shipping-address/$',
                self.shipping_address_view.as_view(), name='shipping-address'),
            url(r'user-address/edit/(?P<pk>\d+)/$',
                self.user_address_update_view.as_view(),
                name='user-address-update'),
            url(r'user-address/delete/(?P<pk>\d+)/$',
                self.user_address_delete_view.as_view(),
                name='user-address-delete'),

            # Payment views
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


application = CheckoutApplication()
