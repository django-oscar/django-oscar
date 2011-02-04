from django.conf.urls.defaults import *

from oscar.checkout.views import SubmitView

def submit_view(request, *args, **kwargs):
    return SubmitView()(request, *args, **kwargs)

urlpatterns = patterns('oscar.checkout.views',
    url(r'^$', 'index', name='oscar-checkout-index'),
    url(r'shipping-address/$', 'shipping_address', name='oscar-checkout-shipping-address'),
    url(r'shipping-method/$', 'shipping_method', name='oscar-checkout-shipping-method'),
    url(r'payment/$', 'payment', name='oscar-checkout-payment'),
    url(r'preview/$', 'preview', name='oscar-checkout-preview'),
    url(r'submit/$', submit_view, name='oscar-checkout-submit'),
    url(r'thank-you/$', 'thank_you', name='oscar-checkout-thank-you'),
)

