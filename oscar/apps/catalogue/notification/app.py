from oscar.core.application import Application
from django.conf.urls.defaults import patterns, url
from oscar.apps.catalogue.notification import views


class ProductNotificationApplication(Application):
    name = None
    confirm_view = views.ConfirmNotificationView
    unsubscribe_view = views.UnsubscribeNotificationView
    create_view = views.CreateProductNotificationView
    #delete_view = views.DeleteProductNotificationView

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^confirm/(?P<key>[a-z0-9]+)/$', self.confirm_view.as_view(),
                name='notification-confirm'),
            url(r'^unsubscribe/(?P<key>[a-z0-9]+)/$', self.unsubscribe_view.as_view(),
                name='notification-unsubscribe'),
            url(r'^add/$', self.create_view.as_view(),
                name='notification-add'),
            #url(r'^remove/$',
            #    self.delete_view.as_view(),
            #    name='notification-remove'),
        )
        return urlpatterns


application = ProductNotificationApplication()
