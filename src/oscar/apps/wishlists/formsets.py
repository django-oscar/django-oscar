# -*- coding: utf-8 -*-
from django.forms.models import inlineformset_factory

from oscar.core.loading import get_class, get_model

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')
WishListLineForm = get_class('wishlists.forms', 'WishListLineForm')


LineFormset = inlineformset_factory(
    WishList, Line, fields=('quantity', ), form=WishListLineForm,
    extra=0, can_delete=False)
