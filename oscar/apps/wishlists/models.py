# -*- coding: utf-8 -*-
from oscar.core.loading import is_model_registered

from .abstract_models import *  # noqa


if not is_model_registered('wishlists', 'WishList'):
    class WishList(AbstractWishList):
        pass


if not is_model_registered('wishlists', 'Line'):
    class Line(AbstractLine):
        pass
