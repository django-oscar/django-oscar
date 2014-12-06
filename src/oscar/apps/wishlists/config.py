from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WishlistsConfig(AppConfig):
    label = 'wishlists'
    name = 'oscar.apps.wishlists'
    verbose_name = _('Wishlists')
