from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PromotionsConfig(AppConfig):
    label = 'promotions'
    name = 'oscar.apps.promotions'
    verbose_name = _('Promotions')
