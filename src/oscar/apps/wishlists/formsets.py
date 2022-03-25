# -*- coding: utf-8 -*-
from django.forms.models import inlineformset_factory

from oscar.core.loading import get_classes, get_model

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')
WishListSharedEmail = get_model('wishlists', 'WishListSharedEmail')

WishListLineForm, WishListSharedEmailForm = get_classes(
    'wishlists.forms', ('WishListLineForm', 'WishListSharedEmailForm'))


LineFormset = inlineformset_factory(
    WishList, Line, fields=('quantity', ), form=WishListLineForm,
    extra=0, can_delete=False)
WishListSharedEmailFormset = inlineformset_factory(
    WishList, WishListSharedEmail, fields=('email', ), form=WishListSharedEmailForm,
    extra=3, can_delete=True)
