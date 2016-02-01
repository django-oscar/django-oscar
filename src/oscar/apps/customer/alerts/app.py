# vim: ts=4:sw=4:expandtabs

__author__ = 'zmott@fantasyflightgames.com'

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from oscar.core.application import Application
from oscar.core.loading import get_class


class AlertsApplication(Application):
    name = None
    hideable_feature_name = 'alerts'

    alert_list_view = get_class('customer.alerts.views',
                                'ProductAlertListView')
    alert_create_view = get_class('customer.alerts.views',
                                  'ProductAlertCreateView')
    alert_confirm_view = get_class('customer.alerts.views',
                                   'ProductAlertConfirmView')
    alert_cancel_view = get_class('customer.alerts.views',
                                  'ProductAlertCancelView')

    def get_urls(self):
        # Alerts can be setup by anonymous users: some views
        # do not require login
        urls = [
            url(r'^$',
                login_required(self.alert_list_view.as_view()),
                name='alerts-list'),
            url(r'^create/(?P<pk>\d+)/$',
                self.alert_create_view.as_view(),
                name='alert-create'),
            url(r'^confirm/(?P<key>[a-z0-9]+)/$',
                self.alert_confirm_view.as_view(),
                name='alerts-confirm'),
            url(r'^cancel/key/(?P<key>[a-z0-9]+)/$',
                self.alert_cancel_view.as_view(),
                name='alerts-cancel-by-key'),
            url(r'^cancel/(?P<pk>[a-z0-9]+)/$',
                login_required(self.alert_cancel_view.as_view()),
                name='alerts-cancel-by-pk')
        ]
        return self.post_process_urls(urls)


application = AlertsApplication()