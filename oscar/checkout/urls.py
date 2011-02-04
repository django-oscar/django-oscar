from django.conf.urls.defaults import *

from oscar.views import class_based_view
from oscar.checkout.views import IndexView, SubmitView

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', class_based_view(IndexView), name='oscar-checkout-index'),
    url(r'shipping-address/$', 'shipping_address', name='oscar-checkout-shipping-address'),
    url(r'shipping-method/$', 'shipping_method', name='oscar-checkout-shipping-method'),
    url(r'payment/$', 'payment', name='oscar-checkout-payment'),
    url(r'preview/$', 'preview', name='oscar-checkout-preview'),
    url(r'submit/$', class_based_view(SubmitView), name='oscar-checkout-submit'),
    url(r'thank-you/$', 'thank_you', name='oscar-checkout-thank-you'),
)

