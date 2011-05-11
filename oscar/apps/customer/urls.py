from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from oscar.core.decorators import class_based_view
from oscar.core.loading import import_module
import_module('customer.views', ['OrderHistoryView', 'OrderDetailView', 'OrderLineView',
                                 'AddressBookView', 'AddressView'], locals())

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'admin/login.html'}, name='oscar-customer-login'),
    url(r'^logout/$', 'login', name='oscar-customer-logout'),
)

urlpatterns += patterns('oscar.apps.customer.views',
    url(r'^profile/$', 'profile', name='oscar-customer-profile'),
    url(r'^order-history/$', OrderHistoryView.as_view(), name='oscar-customer-order-history'),
    url(r'^order/(?P<order_number>[\w-]*)/$', login_required(class_based_view(OrderDetailView)), name='oscar-customer-order-view'),
    url(r'^order/(?P<order_number>[\w-]*)/line/(?P<line_id>\w+)$', login_required(class_based_view(OrderLineView)), name='oscar-customer-order-line'),
    url(r'^address-book/$', AddressBookView.as_view(), name='oscar-customer-address-book'),
    url(r'^address/(?P<address_id>\d+)/$', login_required(class_based_view(AddressView)), name='oscar-customer-address'),
)
