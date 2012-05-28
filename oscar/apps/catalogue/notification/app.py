from django.db.models import get_model
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from oscar.core.application import Application
from oscar.apps.catalogue.notification import views

ProductNotification = get_model('notification', 'productnotification')


class ProductNotificationApplication(Application):
    name = None
    confirm_view = views.ConfirmNotificationView
    unsubscribe_view = views.UnsubscribeNotificationView
    create_view = views.CreateProductNotificationView
    update_view = views.SetStatusProductNotificationView
    delete_view = views.DeleteProductNotificationView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^confirm/(?P<key>[a-z0-9]{40})/$', self.confirm_view.as_view(),
                name='notification-confirm'),
            url(r'^unsubscribe/(?P<key>[a-z0-9]{40})/$', self.unsubscribe_view.as_view(),
                name='notification-unsubscribe'),
            url(r'^add/$', self.create_view.as_view(),
                name='notification-add'),
            url(r'^set-status/(?P<pk>\d+)/(?P<status>%s)/$' % (
                    '|'.join([x[0] for x in ProductNotification.STATUS_TYPES])
                ),
                login_required(self.update_view.as_view()),
                name='notification-set-status'),
            url(r'^remove/(?P<pk>\d+)/$', login_required(self.delete_view.as_view()),
                name='notification-remove'),
        )
        return urlpatterns


application = ProductNotificationApplication()
