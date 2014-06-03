from django.conf.urls import url

from oscar.core.application import Application
from oscar.core.loading import get_class


class ShippingDashboardApplication(Application):
    name = None
    default_permissions = ['is_staff']

    weight_method_list_view = get_class(
        'dashboard.shipping.views', 'WeightBasedListView')

    def get_urls(self):
        urlpatterns = [
            url(r'^weight-based/$', self.weight_method_list_view.as_view(),
                name='shipping-method-list'),
        ]
        return self.post_process_urls(urlpatterns)


application = ShippingDashboardApplication()
