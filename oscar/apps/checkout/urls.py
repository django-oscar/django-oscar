from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
import_module('checkout.views', ['IndexView', 'ShippingAddressView', 'UserAddressDeleteView', 'UserAddressCreateView', 
                                 'UserAddressUpdateView', 'ShippingMethodView', 'PaymentMethodView', 'OrderPreviewView',
                                 'PaymentDetailsView', 'ThankYouView'], locals())

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', IndexView.as_view(), name='oscar-checkout-index'),
    # Shipping/user address views
    url(r'shipping-address/$', ShippingAddressView.as_view(), name='oscar-checkout-shipping-address'),
    url(r'user-address/create/$', UserAddressCreateView.as_view(), name='oscar-checkout-user-address-create'),
    url(r'user-address/edit/(?P<pk>\d+)/$', UserAddressUpdateView.as_view(), name='oscar-checkout-user-address-update'),
    url(r'user-address/delete/(?P<pk>\d+)/$', UserAddressDeleteView.as_view(), name='oscar-checkout-user-address-delete'),
    # Shipping method views
    url(r'shipping-method/$', ShippingMethodView.as_view(), name='oscar-checkout-shipping-method'),
    # Payment method views
    url(r'payment-method/$', PaymentMethodView.as_view(), name='oscar-checkout-payment-method'),
    url(r'preview/$', OrderPreviewView.as_view(), name='oscar-checkout-preview'),
    url(r'payment-details/$', PaymentDetailsView.as_view(), name='oscar-checkout-payment-details'),
    url(r'thank-you/$', ThankYouView.as_view(), name='oscar-checkout-thank-you'),
)

