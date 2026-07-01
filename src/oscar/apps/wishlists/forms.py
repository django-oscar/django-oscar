# -*- coding: utf-8 -*-
from django import forms

from oscar.core.loading import get_model

WishList = get_model("wishlists", "WishList")
Line = get_model("wishlists", "Line")
WishListSharedEmail = get_model("wishlists", "WishListSharedEmail")


class WishListForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = user

    class Meta:
        model = WishList
        fields = ("name", "visibility")


class WishListLineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].widget.attrs["class"] = "input-mini"


class WishListSharedEmailForm(forms.ModelForm):
    class Meta:
        model = WishListSharedEmail
        fields = ("email",)
