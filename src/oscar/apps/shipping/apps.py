from django.utils.translation import gettext_lazy as _

from oscar.core import application


class ShippingConfig(application.OscarConfig):
    label = 'shipping'
    name = 'oscar.apps.shipping'
    verbose_name = _('Shipping')
