# -*- coding: utf-8 -*-
from django import forms
from django.db.models import get_model
from django.forms.models import inlineformset_factory

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')


class WishListForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(WishListForm, self).__init__(*args, **kwargs)
        self.instance.owner = user

    class Meta:
        model = WishList
        fields = ('name', )


LineFormset = inlineformset_factory(WishList, Line, fields=('quantity', ),
                                    extra=0, can_delete=False)
