from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from oscar.apps.customer.views import AccountSummaryView, OrderHistoryView, \
    OrderDetailView, OrderLineView, AddressListView, AddressCreateView, \
    AddressUpdateView, AddressDeleteView, EmailHistoryView, EmailDetailView, \
    AccountAuthView, AnonymousOrderDetailView, ChangePasswordView, ProfileUpdateView, \
    AccountRegistrationView, LogoutView
from oscar.core.application import Application


class CustomerApplication(Application):
    name = 'customer'
    summary_view = AccountSummaryView
    order_history_view = OrderHistoryView
    order_detail_view = OrderDetailView
    anon_order_detail_view = AnonymousOrderDetailView
    order_line_view = OrderLineView
    address_list_view = AddressListView
    address_create_view = AddressCreateView
    address_update_view = AddressUpdateView
    address_delete_view = AddressDeleteView
    email_list_view = EmailHistoryView
    email_detail_view = EmailDetailView
    login_view = AccountAuthView
    logout_view = LogoutView
    register_view = AccountRegistrationView
    profile_update_view = ProfileUpdateView
    change_password_view = ChangePasswordView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', login_required(self.summary_view.as_view()), name='summary'),
            url(r'^login/$', self.login_view.as_view(), name='login'),
            url(r'^logout/$', self.logout_view.as_view(), name='logout'),
            url(r'^register/$', self.register_view.as_view(), name='register'),
            url(r'^change-password/$', self.change_password_view.as_view(),
                name='change-password'),

            # Profile
            url(r'^profile/$', login_required(self.profile_update_view.as_view()), name='profile-update'),
            url(r'^orders/$', login_required(self.order_history_view.as_view()), name='order-list'),
            url(r'^order-status/(?P<order_number>[\w-]*)/(?P<hash>\w+)/$',
                self.anon_order_detail_view.as_view(), name='anon-order'),
            url(r'^orders/(?P<order_number>[\w-]*)/$', login_required(self.order_detail_view.as_view()),
                name='order'),
            url(r'^orders/(?P<order_number>[\w-]*)/(?P<line_id>\d+)$',
                login_required(self.order_line_view.as_view()), name='order-line'),
            url(r'^addresses/$', login_required(self.address_list_view.as_view()),
                name='address-list'),
            url(r'^addresses/add/$', login_required(self.address_create_view.as_view()),
                name='address-create'),
            url(r'^addresses/(?P<pk>\d+)/$', login_required(self.address_update_view.as_view()),
                name='address-detail'),
            url(r'^addresses/(?P<pk>\d+)/delete/$', login_required(self.address_delete_view.as_view()),
                name='address-delete'),
            url(r'^emails/$', login_required(self.email_list_view.as_view()), name='email-list'),
            url(r'^emails/(?P<email_id>\d+)/$', login_required(self.email_detail_view.as_view()),
                name='email-detail'),
            )
        return self.post_process_urls(urlpatterns)


application = CustomerApplication()
