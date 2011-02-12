from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from oscar.views import class_based_view
from oscar.customer.views import OrderHistoryView, OrderDetailView

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'admin/login.html'}, name='oscar-customer-login'),
    url(r'^logout/$', 'login', name='oscar-customer-logout'),
)

urlpatterns = patterns('oscar.customer.views',
    url(r'^profile/$', 'profile', name='oscar-customer-profile'),
    url(r'^order-history/$', OrderHistoryView.as_view(), name='oscar-customer-order-history'),
    url(r'^order/(?P<order_number>[\w-]*)/$', login_required(class_based_view(OrderDetailView)), name='oscar-customer-order-view'),
)