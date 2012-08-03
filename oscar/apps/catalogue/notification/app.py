from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from oscar.core.application import Application
from oscar.apps.catalogue.notification import views
from oscar.apps.catalogue.notification.models import AbstractNotification


class ProductNotificationApplication(Application):
    confirm_view = views.NotificationConfirmView
    unsubscribe_view = views.NotificationUnsubscribeView
    create_view = views.ProductNotificationCreateView
    update_view = views.ProductNotificationSetStatusView
    delete_view = views.ProductNotificationDeleteView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^confirm/(?P<key>[a-z0-9]{40})/$',
                self.confirm_view.as_view(),
                name='notification-confirm'),

            url(r'^unsubscribe/(?P<key>[a-z0-9]{40})/$',
                self.unsubscribe_view.as_view(),
                name='notification-unsubscribe'),

            url(r'^create/$', self.create_view.as_view(),
                name='notification-create'),
            # make sure that only valid status values are allowed in the
            # URL pattern
            url(r'^(?P<pk>\d+)/set-status/(?P<status>%s)/$' % (
                    '|'.join([x[0] for x in AbstractNotification.STATUS_TYPES])
                ),
                login_required(self.update_view.as_view()),
                name='notification-set-status'),

            url(r'^(?P<pk>\d+)/delete/$',
                login_required(self.delete_view.as_view()),
                name='notification-delete'),
        )
        return urlpatterns


application = ProductNotificationApplication()
