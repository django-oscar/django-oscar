from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class OfferConfig(AppConfig):
    label = 'offer'
    name = 'oscar.apps.offer'
    verbose_name = _('Offer')

    def ready(self):
        from . import signals  # noqa
