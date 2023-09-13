from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from django.views import generic

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CustomerConfig(OscarConfig):
    label = "customer"
    name = "oscar.apps.customer"
    verbose_name = _("Customer")

    namespace = "customer"

    # pylint: disable=attribute-defined-outside-init, reimported, unused-import
    def ready(self):
        from . import receivers
        from .alerts import receivers

        self.summary_view = get_class("customer.views", "AccountSummaryView")
        self.order_history_view = get_class("customer.views", "OrderHistoryView")
        self.order_detail_view = get_class("customer.views", "OrderDetailView")
        self.anon_order_detail_view = get_class(
            "customer.views", "AnonymousOrderDetailView"
        )
        self.order_line_view = get_class("customer.views", "OrderLineView")

        self.address_list_view = get_class("customer.views", "AddressListView")
        self.address_create_view = get_class("customer.views", "AddressCreateView")
        self.address_update_view = get_class("customer.views", "AddressUpdateView")
        self.address_delete_view = get_class("customer.views", "AddressDeleteView")
        self.address_change_status_view = get_class(
            "customer.views", "AddressChangeStatusView"
        )

        self.email_list_view = get_class("customer.views", "EmailHistoryView")
        self.email_detail_view = get_class("customer.views", "EmailDetailView")
        self.login_view = get_class("customer.views", "AccountAuthView")
        self.logout_view = get_class("customer.views", "LogoutView")
        self.register_view = get_class("customer.views", "AccountRegistrationView")
        self.profile_view = get_class("customer.views", "ProfileView")
        self.profile_update_view = get_class("customer.views", "ProfileUpdateView")
        self.profile_delete_view = get_class("customer.views", "ProfileDeleteView")
        self.change_password_view = get_class("customer.views", "ChangePasswordView")

        self.notification_inbox_view = get_class(
            "communication.notifications.views", "InboxView"
        )
        self.notification_archive_view = get_class(
            "communication.notifications.views", "ArchiveView"
        )
        self.notification_update_view = get_class(
            "communication.notifications.views", "UpdateView"
        )
        self.notification_detail_view = get_class(
            "communication.notifications.views", "DetailView"
        )

        self.alert_list_view = get_class(
            "customer.alerts.views", "ProductAlertListView"
        )
        self.alert_create_view = get_class(
            "customer.alerts.views", "ProductAlertCreateView"
        )
        self.alert_confirm_view = get_class(
            "customer.alerts.views", "ProductAlertConfirmView"
        )
        self.alert_cancel_view = get_class(
            "customer.alerts.views", "ProductAlertCancelView"
        )

        self.wishlists_add_product_view = get_class(
            "customer.wishlists.views", "WishListAddProduct"
        )
        self.wishlists_list_view = get_class(
            "customer.wishlists.views", "WishListListView"
        )
        self.wishlists_detail_view = get_class(
            "customer.wishlists.views", "WishListDetailView"
        )
        self.wishlists_create_view = get_class(
            "customer.wishlists.views", "WishListCreateView"
        )
        self.wishlists_create_with_product_view = get_class(
            "customer.wishlists.views", "WishListCreateView"
        )
        self.wishlists_update_view = get_class(
            "customer.wishlists.views", "WishListUpdateView"
        )
        self.wishlists_delete_view = get_class(
            "customer.wishlists.views", "WishListDeleteView"
        )
        self.wishlists_remove_product_view = get_class(
            "customer.wishlists.views", "WishListRemoveProduct"
        )
        self.wishlists_move_product_to_another_view = get_class(
            "customer.wishlists.views", "WishListMoveProductToAnotherWishList"
        )

    def get_urls(self):
        urls = [
            # Login, logout and register doesn't require login
            path("login/", self.login_view.as_view(), name="login"),
            path("logout/", self.logout_view.as_view(), name="logout"),
            path("register/", self.register_view.as_view(), name="register"),
            path("", login_required(self.summary_view.as_view()), name="summary"),
            path(
                "change-password/",
                login_required(self.change_password_view.as_view()),
                name="change-password",
            ),
            # Profile
            path(
                "profile/",
                login_required(self.profile_view.as_view()),
                name="profile-view",
            ),
            path(
                "profile/edit/",
                login_required(self.profile_update_view.as_view()),
                name="profile-update",
            ),
            path(
                "profile/delete/",
                login_required(self.profile_delete_view.as_view()),
                name="profile-delete",
            ),
            # Order history
            path(
                "orders/",
                login_required(self.order_history_view.as_view()),
                name="order-list",
            ),
            re_path(
                r"^order-status/(?P<order_number>[\w-]*)/(?P<hash>[A-z0-9-_=:]+)/$",
                self.anon_order_detail_view.as_view(),
                name="anon-order",
            ),
            path(
                "orders/<str:order_number>/",
                login_required(self.order_detail_view.as_view()),
                name="order",
            ),
            path(
                "orders/<str:order_number>/<int:line_id>/",
                login_required(self.order_line_view.as_view()),
                name="order-line",
            ),
            # Address book
            path(
                "addresses/",
                login_required(self.address_list_view.as_view()),
                name="address-list",
            ),
            path(
                "addresses/add/",
                login_required(self.address_create_view.as_view()),
                name="address-create",
            ),
            path(
                "addresses/<int:pk>/",
                login_required(self.address_update_view.as_view()),
                name="address-detail",
            ),
            path(
                "addresses/<int:pk>/delete/",
                login_required(self.address_delete_view.as_view()),
                name="address-delete",
            ),
            re_path(
                r"^addresses/(?P<pk>\d+)/(?P<action>default_for_(billing|shipping))/$",
                login_required(self.address_change_status_view.as_view()),
                name="address-change-status",
            ),
            # Email history
            path(
                "emails/",
                login_required(self.email_list_view.as_view()),
                name="email-list",
            ),
            path(
                "emails/<int:email_id>/",
                login_required(self.email_detail_view.as_view()),
                name="email-detail",
            ),
            # Notifications
            # Redirect to notification inbox
            path(
                "notifications/",
                generic.RedirectView.as_view(
                    url="/accounts/notifications/inbox/", permanent=False
                ),
            ),
            path(
                "notifications/inbox/",
                login_required(self.notification_inbox_view.as_view()),
                name="notifications-inbox",
            ),
            path(
                "notifications/archive/",
                login_required(self.notification_archive_view.as_view()),
                name="notifications-archive",
            ),
            path(
                "notifications/update/",
                login_required(self.notification_update_view.as_view()),
                name="notifications-update",
            ),
            path(
                "notifications/<int:pk>/",
                login_required(self.notification_detail_view.as_view()),
                name="notifications-detail",
            ),
            # Alerts
            # Alerts can be setup by anonymous users: some views do not
            # require login
            path(
                "alerts/",
                login_required(self.alert_list_view.as_view()),
                name="alerts-list",
            ),
            path(
                "alerts/create/<int:pk>/",
                self.alert_create_view.as_view(),
                name="alert-create",
            ),
            path(
                "alerts/confirm/<str:key>/",
                self.alert_confirm_view.as_view(),
                name="alerts-confirm",
            ),
            path(
                "alerts/cancel/key/<str:key>/",
                self.alert_cancel_view.as_view(),
                name="alerts-cancel-by-key",
            ),
            path(
                "alerts/cancel/<int:pk>/",
                login_required(self.alert_cancel_view.as_view()),
                name="alerts-cancel-by-pk",
            ),
            # Wishlists
            path(
                "wishlists/",
                login_required(self.wishlists_list_view.as_view()),
                name="wishlists-list",
            ),
            path(
                "wishlists/add/<int:product_pk>/",
                login_required(self.wishlists_add_product_view.as_view()),
                name="wishlists-add-product",
            ),
            path(
                "wishlists/<str:key>/add/<int:product_pk>/",
                login_required(self.wishlists_add_product_view.as_view()),
                name="wishlists-add-product",
            ),
            path(
                "wishlists/create/",
                login_required(self.wishlists_create_view.as_view()),
                name="wishlists-create",
            ),
            path(
                "wishlists/create/with-product/<int:product_pk>/",
                login_required(self.wishlists_create_view.as_view()),
                name="wishlists-create-with-product",
            ),
            # Wishlists can be publicly shared, no login required
            path(
                "wishlists/<str:key>/",
                self.wishlists_detail_view.as_view(),
                name="wishlists-detail",
            ),
            path(
                "wishlists/<str:key>/update/",
                login_required(self.wishlists_update_view.as_view()),
                name="wishlists-update",
            ),
            path(
                "wishlists/<str:key>/delete/",
                login_required(self.wishlists_delete_view.as_view()),
                name="wishlists-delete",
            ),
            path(
                "wishlists/<str:key>/lines/<int:line_pk>/delete/",
                login_required(self.wishlists_remove_product_view.as_view()),
                name="wishlists-remove-product",
            ),
            path(
                "wishlists/<str:key>/products/<int:product_pk>/delete/",
                login_required(self.wishlists_remove_product_view.as_view()),
                name="wishlists-remove-product",
            ),
            path(
                "wishlists/<str:key>/lines/<int:line_pk>/move-to/<str:to_key>/",
                login_required(self.wishlists_move_product_to_another_view.as_view()),
                name="wishlists-move-product-to-another",
            ),
        ]

        return self.post_process_urls(urls)
