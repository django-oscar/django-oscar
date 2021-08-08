from django.utils.translation import gettext_lazy as _

from oscar.core import application


class OrderConfig(application.OscarConfig):
    label = 'order'
    name = 'oscar.apps.order'
    verbose_name = _('Order')
