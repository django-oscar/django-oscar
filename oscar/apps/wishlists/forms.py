# -*- coding: utf-8 -*-
from django import forms
from django.db.models import get_model
from django.forms.models import inlineformset_factory

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


class WishListForm(forms.ModelForm):
    class Meta:
        model = WishList
        fields = ('name', )


LineFormset = inlineformset_factory(WishList, Line, fields=('quantity', ),
                                    extra=0, can_delete=False)
