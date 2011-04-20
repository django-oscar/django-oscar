from django.conf.urls.defaults import *
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.decorators import class_based_view
from oscar.order_management.views import OrderListView, OrderView

urlpatterns = patterns('oscar.order_management.views',
    url(r'^$', staff_member_required(OrderListView.as_view()), name='oscar-order-management-list'),
    url(r'^order/(?P<order_number>[\w-]*)/$', staff_member_required(class_based_view(OrderView)), name='oscar-order-management-order'),
)

