from django.conf.urls.defaults import *

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module

import_module('checkout.views', ['IndexView', 'ShippingAddressView',
                                 'ShippingMethodView', 'PaymentMethodView', 'OrderPreviewView',
                                 'PaymentDetailsView', 'ThankYouView'], locals())

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', IndexView.as_view(), name='oscar-checkout-index'),
    url(r'shipping-address/$', class_based_view(ShippingAddressView), name='oscar-checkout-shipping-address'),
    url(r'shipping-method/$', class_based_view(ShippingMethodView), name='oscar-checkout-shipping-method'),
    url(r'payment-method/$', class_based_view(PaymentMethodView), name='oscar-checkout-payment-method'),
    url(r'preview/$', class_based_view(OrderPreviewView), name='oscar-checkout-preview'),
    url(r'payment-details/$', class_based_view(PaymentDetailsView), name='oscar-checkout-payment-details'),
    url(r'thank-you/$', class_based_view(ThankYouView), name='oscar-checkout-thank-you'),
)

