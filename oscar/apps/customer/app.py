from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views import generic

from oscar.apps.customer import views
from oscar.apps.customer.notifications import views as notification_views
from oscar.apps.customer.alerts import views as alert_views
from oscar.apps.customer.wishlists import views as wishlists_views
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
    address_change_status_view = views.AddressChangeStatusView

    email_list_view = views.EmailHistoryView
    email_detail_view = views.EmailDetailView
    login_view = views.AccountAuthView
    logout_view = views.LogoutView
    register_view = views.AccountRegistrationView
    profile_view = views.ProfileView
    profile_update_view = views.ProfileUpdateView
    profile_delete_view = views.ProfileDeleteView
    change_password_view = views.ChangePasswordView

    notification_inbox_view = notification_views.InboxView
    notification_archive_view = notification_views.ArchiveView
    notification_update_view = notification_views.UpdateView
    notification_detail_view = notification_views.DetailView

    alert_list_view = alert_views.ProductAlertListView
    alert_create_view = alert_views.ProductAlertCreateView
    alert_confirm_view = alert_views.ProductAlertConfirmView
    alert_cancel_view = alert_views.ProductAlertCancelView

    wishlists_add_product_view = wishlists_views.WishListAddProduct
    wishlists_list_view = wishlists_views.WishListListView
    wishlists_detail_view = wishlists_views.WishListDetailView
    wishlists_create_view = wishlists_views.WishListCreateView
    wishlists_create_with_product_view = wishlists_views.WishListCreateView
    wishlists_update_view = wishlists_views.WishListUpdateView
    wishlists_delete_view = wishlists_views.WishListDeleteView
    wishlists_remove_product_view = wishlists_views.WishListRemoveProduct
    wishlists_move_product_to_another_view \
        = wishlists_views.WishListMoveProductToAnotherWishList

    def get_urls(self):
        urls = [
            url(r'^$', login_required(self.summary_view.as_view()),
                name='summary'),
            url(r'^login/$', self.login_view.as_view(), name='login'),
            url(r'^logout/$', self.logout_view.as_view(), name='logout'),
            url(r'^register/$', self.register_view.as_view(), name='register'),
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
            url(r'^notifications/(?P<pk>\d+)/$',
                login_required(self.notification_detail_view.as_view()),
                name='notifications-detail'),

            # Alerts
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

        return self.post_process_urls(patterns('', *urls))


application = CustomerApplication()
