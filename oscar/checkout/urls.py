from django.conf.urls.defaults import *

from oscar.views import class_based_view
from oscar.checkout.views import (IndexView, ShippingAddressView, SubmitView,
                                  ShippingMethodView, PaymentView, OrderPreviewView,
                                  ThankYouView)

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', class_based_view(IndexView), name='oscar-checkout-index'),
    url(r'shipping-address/$', class_based_view(ShippingAddressView), name='oscar-checkout-shipping-address'),
    url(r'shipping-method/$', class_based_view(ShippingMethodView), name='oscar-checkout-shipping-method'),
    url(r'payment/$', class_based_view(PaymentView), name='oscar-checkout-payment'),
    url(r'preview/$', class_based_view(OrderPreviewView), name='oscar-checkout-preview'),
    url(r'submit/$', class_based_view(SubmitView), name='oscar-checkout-submit'),
    url(r'thank-you/$', class_based_view(ThankYouView), name='oscar-checkout-thank-you'),
)

