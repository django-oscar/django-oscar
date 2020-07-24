from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views import generic

from oscar.core.application import Application
from oscar.core.loading import get_class


class CommunicationApplication(Application):
    name = 'communication'

    alert_list_view = get_class(
        'communication.alerts.views', 'ProductAlertListView')
    alert_create_view = get_class(
        'communication.alerts.views', 'ProductAlertCreateView')
    alert_confirm_view = get_class(
        'communication.alerts.views', 'ProductAlertConfirmView')
    alert_cancel_view = get_class(
        'communication.alerts.views', 'ProductAlertCancelView')

    notification_inbox_view = get_class(
        'communication.notifications.views', 'InboxView')
    notification_archive_view = get_class(
        'communication.notifications.views', 'ArchiveView')
    notification_update_view = get_class(
        'communication.notifications.views', 'UpdateView')
    notification_detail_view = get_class(
        'communication.notifications.views', 'DetailView')

    def get_urls(self):
        urls = [
            # Alerts
            # Alerts can be setup by anonymous users: some views do not
            # require login
            path('alerts/', login_required(self.alert_list_view.as_view()), name='alerts-list'),
            path('alerts/create/<int:pk>/', self.alert_create_view.as_view(), name='alert-create'),
            path('alerts/confirm/<str:key>/', self.alert_confirm_view.as_view(), name='alerts-confirm'),
            path('alerts/cancel/key/<str:key>/', self.alert_cancel_view.as_view(), name='alerts-cancel-by-key'),
            path(
                'alerts/cancel/<int:pk>/',
                login_required(self.alert_cancel_view.as_view()),
                name='alerts-cancel-by-pk'),

            # Notifications
            # Redirect to notification inbox
            path(
                'notifications/', generic.RedirectView.as_view(url='/accounts/notifications/inbox/', permanent=False)),
            path(
                'notifications/inbox/',
                login_required(self.notification_inbox_view.as_view()),
                name='notifications-inbox'),
            path(
                'notifications/archive/',
                login_required(self.notification_archive_view.as_view()),
                name='notifications-archive'),
            path(
                'notifications/update/',
                login_required(self.notification_update_view.as_view()),
                name='notifications-update'),
            path(
                'notifications/<int:pk>/',
                login_required(self.notification_detail_view.as_view()),
                name='notifications-detail'),
        ]

        return self.post_process_urls(urls)


application = CommunicationApplication()
