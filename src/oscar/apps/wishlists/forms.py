# -*- coding: utf-8 -*-
from django import forms
from django.forms.models import inlineformset_factory

from oscar.core.loading import get_model

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


class WishListForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(WishListForm, self).__init__(*args, **kwargs)
        self.instance.owner = user

    class Meta:
        model = WishList
        fields = ('name', )


class WishListLineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(WishListLineForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['class'] = 'input-mini'


LineFormset = inlineformset_factory(
    WishList, Line, fields=('quantity', ), form=WishListLineForm,
    extra=0, can_delete=False)
