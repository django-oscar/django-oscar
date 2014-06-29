# -*- coding: utf-8 -*-
from django.conf import settings

from .abstract_models import *  # noqa


if 'wishlists.WishList' not in settings.OSCAR_OVERRIDE_MODELS:
    class WishList(AbstractWishList):
        pass


if 'wishlists.Line' not in settings.OSCAR_OVERRIDE_MODELS:
    class Line(AbstractLine):
        pass
