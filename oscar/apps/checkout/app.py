from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.conf import settings

from oscar.core.application import Application
from oscar.apps.checkout.views import IndexView, ShippingAddressView, UserAddressDeleteView, UserAddressCreateView, \
                                      UserAddressUpdateView, ShippingMethodView, PaymentMethodView, OrderPreviewView, \
                                      PaymentDetailsView, ThankYouView


class CheckoutApplication(Application):
    name = 'checkout'
    
    index_view = IndexView
    shipping_address_view = ShippingAddressView
    user_address_create_view = UserAddressCreateView
    user_address_update_view = UserAddressUpdateView
    user_address_delete_view = UserAddressDeleteView
    shipping_method_view = ShippingMethodView
    payment_method_view = PaymentMethodView
    order_preview_view = OrderPreviewView
    payment_details_view = PaymentDetailsView
    thankyou_view = ThankYouView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index_view.as_view(), name='index'),
            # Shipping/user address views
            url(r'shipping-address/$', self.shipping_address_view.as_view(), name='shipping-address'),
            url(r'user-address/create/$', self.user_address_create_view.as_view(), name='user-address-create'),
            url(r'user-address/edit/(?P<pk>\d+)/$', self.user_address_update_view.as_view(), name='user-address-update'),
            url(r'user-address/delete/(?P<pk>\d+)/$', self.user_address_delete_view.as_view(), name='user-address-delete'),
            # Shipping method views
            url(r'shipping-method/$', self.shipping_method_view.as_view(), name='shipping-method'),
            # Payment method views
            url(r'payment-method/$', self.payment_method_view.as_view(), name='payment-method'),
            url(r'preview/$', self.order_preview_view.as_view(), name='preview'),
            url(r'payment-details/$', self.payment_details_view.as_view(), name='payment-details'),
            url(r'thank-you/$', self.thankyou_view.as_view(), name='thank-you'),
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, pattern):
        if pattern.name == 'index':
            return None
        if not settings.OSCAR_ALLOW_ANON_CHECKOUT:
            return login_required
        if pattern.name.startswith('user-address'):
            return login_required
        return None

application = CheckoutApplication()