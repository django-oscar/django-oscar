from django.conf.urls.defaults import *

from oscar.views import class_based_view
from oscar.order_management.views import OrderListView, OrderView

urlpatterns = patterns('oscar.order_management.views',
    url(r'^$', OrderListView.as_view(), name='oscar-order-management-list'),
    url(r'^order/(?P<order_number>[\w-]*)/$', class_based_view(OrderView), name='oscar-order-management-order'),
)

