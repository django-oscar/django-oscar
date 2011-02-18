from django.conf.urls.defaults import *

from oscar.views import class_based_view
from oscar.services import import_module

checkout_views = import_module('checkout.views', ['IndexView', 'ShippingAddressView', 'SubmitView',
                                                  'ShippingMethodView', 'PaymentMethodView', 'OrderPreviewView',
                                                  'PaymentDetailsView', 'ThankYouView'])

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', class_based_view(checkout_views.IndexView), name='oscar-checkout-index'),
    url(r'shipping-address/$', class_based_view(checkout_views.ShippingAddressView), name='oscar-checkout-shipping-address'),
    url(r'shipping-method/$', class_based_view(checkout_views.ShippingMethodView), name='oscar-checkout-shipping-method'),
    url(r'payment-method/$', class_based_view(checkout_views.PaymentMethodView), name='oscar-checkout-payment-method'),
    url(r'preview/$', class_based_view(checkout_views.OrderPreviewView), name='oscar-checkout-preview'),
    url(r'payment-details/$', class_based_view(checkout_views.PaymentDetailsView), name='oscar-checkout-payment-details'),
    url(r'submit/$', class_based_view(checkout_views.SubmitView), name='oscar-checkout-submit'),
    url(r'thank-you/$', class_based_view(checkout_views.ThankYouView), name='oscar-checkout-thank-you'),
)

