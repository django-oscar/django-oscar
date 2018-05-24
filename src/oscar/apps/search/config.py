from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    label = 'search'
    name = 'oscar.apps.search'
    verbose_name = _('Search')
