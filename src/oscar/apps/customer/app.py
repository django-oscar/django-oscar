from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views import generic

from oscar.core.application import Application
from oscar.core.loading import get_class


class CustomerApplication(Application):
    name = 'customer'
    summary_view = get_class('customer.views', 'AccountSummaryView')
    order_history_view = get_class('customer.views', 'OrderHistoryView')
    order_detail_view = get_class('customer.views', 'OrderDetailView')
    anon_order_detail_view = get_class('customer.views',
                                       'AnonymousOrderDetailView')
    order_line_view = get_class('customer.views', 'OrderLineView')

    address_list_view = get_class('customer.views', 'AddressListView')
    address_create_view = get_class('customer.views', 'AddressCreateView')
    address_update_view = get_class('customer.views', 'AddressUpdateView')
    address_delete_view = get_class('customer.views', 'AddressDeleteView')
    address_change_status_view = get_class('customer.views',
                                           'AddressChangeStatusView')

    email_list_view = get_class('customer.views', 'EmailHistoryView')
    email_detail_view = get_class('customer.views', 'EmailDetailView')
    login_view = get_class('customer.views', 'AccountAuthView')
    logout_view = get_class('customer.views', 'LogoutView')
    register_view = get_class('customer.views', 'AccountRegistrationView')
    profile_view = get_class('customer.views', 'ProfileView')
    profile_update_view = get_class('customer.views', 'ProfileUpdateView')
    profile_delete_view = get_class('customer.views', 'ProfileDeleteView')
    change_password_view = get_class('customer.views', 'ChangePasswordView')

    notification_inbox_view = get_class('customer.notifications.views',
                                        'InboxView')
    notification_archive_view = get_class('customer.notifications.views',
                                          'ArchiveView')
    notification_update_view = get_class('customer.notifications.views',
                                         'UpdateView')
    notification_detail_view = get_class('customer.notifications.views',
                                         'DetailView')

    alert_list_view = get_class('customer.alerts.views',
                                'ProductAlertListView')
    alert_create_view = get_class('customer.alerts.views',
                                  'ProductAlertCreateView')
    alert_confirm_view = get_class('customer.alerts.views',
                                   'ProductAlertConfirmView')
    alert_cancel_view = get_class('customer.alerts.views',
                                  'ProductAlertCancelView')

    wishlists_add_product_view = get_class('customer.wishlists.views',
                                           'WishListAddProduct')
    wishlists_list_view = get_class('customer.wishlists.views',
                                    'WishListListView')
    wishlists_detail_view = get_class('customer.wishlists.views',
                                      'WishListDetailView')
    wishlists_create_view = get_class('customer.wishlists.views',
                                      'WishListCreateView')
    wishlists_create_with_product_view = get_class('customer.wishlists.views',
                                                   'WishListCreateView')
    wishlists_update_view = get_class('customer.wishlists.views',
                                      'WishListUpdateView')
    wishlists_delete_view = get_class('customer.wishlists.views',
                                      'WishListDeleteView')
    wishlists_remove_product_view = get_class('customer.wishlists.views',
                                              'WishListRemoveProduct')
    wishlists_move_product_to_another_view = get_class(
        'customer.wishlists.views', 'WishListMoveProductToAnotherWishList')

    def get_urls(self):
        urls = [
            # Login, logout and register doesn't require login
            url(r'^login/$', self.login_view.as_view(), name='login'),
            url(r'^logout/$', self.logout_view.as_view(), name='logout'),
            url(r'^register/$', self.register_view.as_view(), name='register'),
            url(r'^$', login_required(self.summary_view.as_view()),
                name='summary'),
            url(r'^change-password/$',
                login_required(self.change_password_view.as_view()),
                name='change-password'),

            # Profile
            url(r'^profile/$',
                login_required(self.profile_view.as_view()),
                name='profile-view'),
            url(r'^profile/edit/$',
                login_required(self.profile_update_view.as_view()),
                name='profile-update'),
            url(r'^profile/delete/$',
                login_required(self.profile_delete_view.as_view()),
                name='profile-delete'),

            # Order history
            url(r'^orders/$',
                login_required(self.order_history_view.as_view()),
                name='order-list'),
            url(r'^order-status/(?P<order_number>[\w-]*)/(?P<hash>[A-z0-9-_=:]+)/$',
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
            url(r'^addresses/(?P<pk>\d+)/'
                r'(?P<action>default_for_(billing|shipping))/$',
                login_required(self.address_change_status_view.as_view()),
                name='address-change-status'),

            # Email history
            url(r'^emails/$',
                login_required(self.email_list_view.as_view()),
                name='email-list'),
            url(r'^emails/(?P<email_id>\d+)/$',
                login_required(self.email_detail_view.as_view()),
                name='email-detail'),

            # Notifications
            # Redirect to notification inbox
            url(r'^notifications/$', generic.RedirectView.as_view(
                url='/accounts/notifications/inbox/', permanent=False)),
            url(r'^notifications/inbox/$',
                login_required(self.notification_inbox_view.as_view()),
                name='notifications-inbox'),
            url(r'^notifications/archive/$',
                login_required(self.notification_archive_view.as_view()),
                name='notifications-archive'),
            url(r'^notifications/update/$',
                login_required(self.notification_update_view.as_view()),
                name='notifications-update'),
            url(r'^notifications/(?P<pk>\d+)/$',
                login_required(self.notification_detail_view.as_view()),
                name='notifications-detail'),

            # Alerts
            # Alerts can be setup by anonymous users: some views do not
            # require login
            url(r'^alerts/$',
                login_required(self.alert_list_view.as_view()),
                name='alerts-list'),
            url(r'^alerts/create/(?P<pk>\d+)/$',
                self.alert_create_view.as_view(),
                name='alert-create'),
            url(r'^alerts/confirm/(?P<key>[a-z0-9]+)/$',
                self.alert_confirm_view.as_view(),
                name='alerts-confirm'),
            url(r'^alerts/cancel/key/(?P<key>[a-z0-9]+)/$',
                self.alert_cancel_view.as_view(),
                name='alerts-cancel-by-key'),
            url(r'^alerts/cancel/(?P<pk>[a-z0-9]+)/$',
                login_required(self.alert_cancel_view.as_view()),
                name='alerts-cancel-by-pk'),

            # Wishlists
            url(r'wishlists/$',
                login_required(self.wishlists_list_view.as_view()),
                name='wishlists-list'),
            url(r'wishlists/add/(?P<product_pk>\d+)/$',
                login_required(self.wishlists_add_product_view.as_view()),
                name='wishlists-add-product'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/add/(?P<product_pk>\d+)/',
                login_required(self.wishlists_add_product_view.as_view()),
                name='wishlists-add-product'),
            url(r'wishlists/create/$',
                login_required(self.wishlists_create_view.as_view()),
                name='wishlists-create'),
            url(r'wishlists/create/with-product/(?P<product_pk>\d+)/$',
                login_required(self.wishlists_create_view.as_view()),
                name='wishlists-create-with-product'),
            # Wishlists can be publicly shared, no login required
            url(r'wishlists/(?P<key>[a-z0-9]+)/$',
                self.wishlists_detail_view.as_view(), name='wishlists-detail'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/update/$',
                login_required(self.wishlists_update_view.as_view()),
                name='wishlists-update'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/delete/$',
                login_required(self.wishlists_delete_view.as_view()),
                name='wishlists-delete'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/lines/(?P<line_pk>\d+)/delete/',
                login_required(self.wishlists_remove_product_view.as_view()),
                name='wishlists-remove-product'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/products/(?P<product_pk>\d+)/'
                r'delete/',
                login_required(self.wishlists_remove_product_view.as_view()),
                name='wishlists-remove-product'),
            url(r'wishlists/(?P<key>[a-z0-9]+)/lines/(?P<line_pk>\d+)/move-to/'
                r'(?P<to_key>[a-z0-9]+)/$',
                login_required(self.wishlists_move_product_to_another_view
                               .as_view()),
                name='wishlists-move-product-to-another')]

        return self.post_process_urls(urls)


application = CustomerApplication()
