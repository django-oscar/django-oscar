from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.conf import settings

from oscar.core.application import Application
from oscar.apps.checkout import views


class CheckoutApplication(Application):
    name = 'checkout'

    index_view = views.IndexView
    shipping_address_view = views.ShippingAddressView
    user_address_update_view = views.UserAddressUpdateView
    user_address_delete_view = views.UserAddressDeleteView
    shipping_method_view = views.ShippingMethodView
    payment_method_view = views.PaymentMethodView
    payment_details_view = views.PaymentDetailsView
    thankyou_view = views.ThankYouView

    def get_urls(self):
        urlpatterns = patterns('',
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

            # Payment method views
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
        )
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, pattern):
        if not settings.OSCAR_ALLOW_ANON_CHECKOUT:
            return login_required
        if pattern.name.startswith('user-address'):
            return login_required
        return None


application = CheckoutApplication()
