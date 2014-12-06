from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ShippingDashboardConfig(AppConfig):
    label = 'shipping_dashboard'
    name = 'oscar.apps.dashboard.shipping'
    verbose_name = _('Shipping dashboard')
