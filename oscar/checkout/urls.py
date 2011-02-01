from django.conf.urls.defaults import *

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', 'index', name='oscar-checkout-index'),
    url(r'delivery_address/$', 'delivery_address', name='oscar-checkout-delivery-address'),
    url(r'delivery_method/$', 'delivery_method', name='oscar-checkout-delivery-method'),
    url(r'payment/$', 'payment', name='oscar-checkout-payment'),
    url(r'preview/$', 'preview', name='oscar-checkout-preview'),
    url(r'submit/$', 'submit', name='oscar-checkout-submit'),
    url(r'thank_you/$', 'thank_you', name='oscar-checkout-thank-you'),
)

