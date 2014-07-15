# -*- coding: utf-8 -*-
from oscar.core.loading import model_registered

from .abstract_models import *  # noqa


if not model_registered('wishlists', 'WishList'):
    class WishList(AbstractWishList):
        pass


if not model_registered('wishlists', 'Line'):
    class Line(AbstractLine):
        pass
