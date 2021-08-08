from django.utils.translation import gettext_lazy as _

from oscar.core import application


class AddressConfig(application.OscarConfig):
    label = 'address'
    name = 'oscar.apps.address'
    verbose_name = _('Address')
