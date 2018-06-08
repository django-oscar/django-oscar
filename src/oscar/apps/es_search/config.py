from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    label = 'es_search'
    name = 'oscar.apps.es_search'
    verbose_name = _('Search')
