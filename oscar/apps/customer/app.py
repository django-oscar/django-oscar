from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views import generic

from oscar.apps.customer import views
from oscar.apps.customer.notifications import views as notification_views
from oscar.apps.customer.alerts import views as alert_views
from oscar.core.application import Application


class CustomerApplication(Application):
    name = 'customer'
    summary_view = views.AccountSummaryView
    order_history_view = views.OrderHistoryView
    order_detail_view = views.OrderDetailView
    anon_order_detail_view = views.AnonymousOrderDetailView
    order_line_view = views.OrderLineView
    address_list_view = views.AddressListView
    address_create_view = views.AddressCreateView
    address_update_view = views.AddressUpdateView
    address_delete_view = views.AddressDeleteView
    email_list_view = views.EmailHistoryView
    email_detail_view = views.EmailDetailView
    login_view = views.AccountAuthView
    logout_view = views.LogoutView
    register_view = views.AccountRegistrationView
    profile_update_view = views.ProfileUpdateView
    change_password_view = views.ChangePasswordView

    notification_inbox_view = notification_views.InboxView
    notification_archive_view = notification_views.ArchiveView
    notification_update_view = notification_views.UpdateView

    alert_create_view = alert_views.ProductAlertCreateView
    alert_confirm_view = alert_views.ProductAlertConfirmView
    alert_cancel_view = alert_views.ProductAlertCancelView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', login_required(self.summary_view.as_view()),
                name='summary'),
            url(r'^login/$', self.login_view.as_view(), name='login'),
            url(r'^logout/$', self.logout_view.as_view(), name='logout'),
            url(r'^register/$', self.register_view.as_view(), name='register'),
            url(r'^change-password/$', self.change_password_view.as_view(),
                name='change-password'),

            # Profile
            url(r'^profile/$',
                login_required(self.profile_update_view.as_view()),
                name='profile-update'),

            # Order history
            url(r'^orders/$',
                login_required(self.order_history_view.as_view()),
                name='order-list'),
            url(r'^order-status/(?P<order_number>[\w-]*)/(?P<hash>\w+)/$',
                self.anon_order_detail_view.as_view(), name='anon-order'),
            url(r'^orders/(?P<order_number>[\w-]*)/$',
                login_required(self.order_detail_view.as_view()),
                name='order'),
            url(r'^orders/(?P<order_number>[\w-]*)/(?P<line_id>\d+)$',
                login_required(self.order_line_view.as_view()),
                name='order-line'),

            # Address book
            url(r'^addresses/$',
                login_required(self.address_list_view.as_view()),
                name='address-list'),
            url(r'^addresses/add/$',
                login_required(self.address_create_view.as_view()),
                name='address-create'),
            url(r'^addresses/(?P<pk>\d+)/$',
                login_required(self.address_update_view.as_view()),
                name='address-detail'),
            url(r'^addresses/(?P<pk>\d+)/delete/$',
                login_required(self.address_delete_view.as_view()),
                name='address-delete'),

            # Email history
            url(r'^emails/$',
                login_required(self.email_list_view.as_view()),
                name='email-list'),
            url(r'^emails/(?P<email_id>\d+)/$',
                login_required(self.email_detail_view.as_view()),
                name='email-detail'),

            # Notifications
            url(r'^notifications/$', generic.RedirectView.as_view(
                url='/accounts/notifications/inbox/')),
            url(r'^notifications/inbox/$',
                login_required(self.notification_inbox_view.as_view()),
                name='notifications-inbox'),
            url(r'^notifications/archive/$',
                login_required(self.notification_archive_view.as_view()),
                name='notifications-archive'),
            url(r'^notifications/update/$',
                login_required(self.notification_update_view.as_view()),
                name='notifications-update'),

            # Alerts
            url(r'^alerts/create/(?P<pk>\d+)/$', self.alert_create_view.as_view(),
                name='alert-create'),
            url(r'^alerts/confirm/(?P<key>[a-z0-9]+)/$',
                self.alert_confirm_view.as_view(),
                name='alerts-confirm'),
            url(r'^alerts/cancel/(?P<key>[a-z0-9]+)/$',
                self.alert_cancel_view.as_view(),
                name='alerts-cancel'),
            )
        return self.post_process_urls(urlpatterns)


application = CustomerApplication()
