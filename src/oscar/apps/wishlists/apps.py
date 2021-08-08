from django.utils.translation import gettext_lazy as _

from oscar.core import application


class WishlistsConfig(application.OscarConfig):
    label = 'wishlists'
    name = 'oscar.apps.wishlists'
    verbose_name = _('Wishlists')
