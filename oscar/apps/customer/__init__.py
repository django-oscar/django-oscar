from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth.decorators import login_required
from oscar.apps.customer.views import AccountSummaryView, OrderHistoryView, \
    OrderHistoryView, OrderDetailView, OrderLineView, AddressListView, AddressUpdateView, AddressDeleteView
from oscar.core.application import Application

class CustomerApplication(Application):
    name = 'customer'
    summary_view = AccountSummaryView
    order_history_view = OrderHistoryView
    order_detail_view = OrderDetailView
    order_line_view = OrderLineView
    address_list_view = AddressListView
    address_update_view = AddressUpdateView
    address_delete_view = AddressDeleteView 

    def get_urls(self):
        urlpatterns = patterns('django.contrib.auth.views',
            url(r'^login/$', 'login', {'template_name': 'admin/login.html'}, name='login'),
            url(r'^logout/$', 'login', name='logout'),
        )
        
        urlpatterns += patterns('',
            url(r'^$', login_required(self.summary_view.as_view()), name='summary'),
            url(r'^orders/$', login_required(self.order_history_view.as_view()), name='order-list'),
            url(r'^orders/(?P<order_number>[\w-]*)/$', login_required(self.order_detail_view.as_view()), name='order'),
            url(r'^orders/(?P<order_number>[\w-]*)/(?P<line_id>\w+)$', login_required(self.order_line_view), name='order-line'),
            url(r'^addresses/$', login_required(self.address_list_view.as_view()), name='address-list'),
            url(r'^addresses/(?P<pk>\d+)/$', login_required(self.address_update_view.as_view()), name='address'),
            url(r'^addresses/(?P<pk>\d+)/delete/$', login_required(self.address_delete_view.as_view()), name='address-delete'),            
        )
        return urlpatterns

application = CustomerApplication()