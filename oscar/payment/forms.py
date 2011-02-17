# -*- coding: utf-8 -*-
from django import forms

class BankcardForm(forms.Form):
    
    number = forms.CharField(max_length=16)
    name = forms.CharField(max_length=128)
    