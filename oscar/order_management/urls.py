from django.conf.urls.defaults import *

from oscar.order_management.views import OrderListView, OrderDetailView

urlpatterns = patterns('oscar.order_management.views',
    url(r'^$', OrderListView.as_view(), name='oscar-order-management-list'),
    url(r'^order/(?P<order_number>[\w-]*)$', OrderDetailView.as_view(), name='oscar-order-management-order'),
)

