from oscar.core.application import Application
from django.conf.urls.defaults import patterns, url, include
from oscar.apps.catalogue.notification.views import CreateProductNotificationView


class ProductNotificationApplication(Application):
    name = None
    #confirm_view = ConfirmNotificationView
    #unsubscribe_view = views.UnsubscribeNotificationView
    create_view = CreateProductNotificationView
    #delete_view = views.DeleteProductNotificationView

    def get_urls(self):
        urlpatterns = patterns('',
            #url(r'^confirm/(?P<key>[A-Z]+)/$',
            #    self.confirm_view.as_view(),
            #    name='notification-confirm'),
            #url(r'^unsubscribe/(?P<key>[A-Z]+)/$',
            #    self.unsubscribe_view.as_view(),
            #    name='notification-unsubscribe'),
            url(r'^add/$', self.create_view.as_view(),
                name='notification-add'),
            #url(r'^remove/$',
            #    self.delete_view.as_view(),
            #    name='notification-remove'),
        )
        return urlpatterns


application = ProductNotificationApplication()
