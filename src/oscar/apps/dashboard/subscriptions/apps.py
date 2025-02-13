from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class SubscriptionsDashboardConfig(OscarDashboardConfig):
    label = "subscriptions_dashboard"
    name = "oscar.apps.dashboard.subscriptions"
    verbose_name = _("Subscriptions dashboard")

    # pylint: disable=attribute-defined-outside-init
    def ready(self):
        self.subscription_view = get_class("dashboard.subscriptions.views", "SubscriptionsListView")
        self.cancel_subscription_view = get_class("dashboard.subscriptions.views", "CancelSubscriptionView")
        self.cancel_subscription = get_class(
            "dashboard.subscriptions.views", "CancelSubscription"
        )
        self.reactivate_subscription_view = get_class("dashboard.subscriptions.views", "ReactivateSubscriptionView")
        self.subscripe_view = get_class("dashboard.subscriptions.views", "SubscribeView")
        self.change_subscription_view = get_class(
            "dashboard.subscriptions.views", "ChangeSubscriptionView"
        )
        self.update_subscription_view = get_class(
            "dashboard.subscriptions.views", "UpdateBranchesView"
        )
        self.renew_subscription_view = get_class("dashboard.subscriptions.views", "RenewSubscriptionView")

    def get_urls(self):
        urls = [
            path(
                "",
                self.subscription_view.as_view(),
                name="subscription-view",
            ),
            path(
                "cancel/",
                self.cancel_subscription_view.as_view(),
                name="cancel-subscription-view",
            ),
            path(
                "cancel/confirm/",
                self.cancel_subscription.as_view(),
                name="cancel-subscription",
            ),
            path(
                "reactivate/",
                self.reactivate_subscription_view.as_view(),
                name="reactivate-subscription-view",
            ),
            path(
                "subscribe/",
                self.subscripe_view.as_view(),
                name="subscribe-view",
            ),
            path(
                "change/",
                self.change_subscription_view.as_view(),
                name="change-subscription-view",
            ),
            path(
                "update-branches/",
                self.update_subscription_view.as_view(),
                name="update-subscription-view",
            ),
            path(
                "renew/",
                self.renew_subscription_view.as_view(),
                name="renew-subscription-view",
            ),
        ]
        return self.post_process_urls(urls)
