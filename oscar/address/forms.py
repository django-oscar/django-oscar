# -*- coding: utf-8 -*-
from django.forms import ModelForm

from oscar.services import import_module
address_models = import_module('address.models', ['UserAddress'])


class UserAddressForm(ModelForm):

    class Meta:
        model = address_models.UserAddress
        exclude = ('user', 'num_orders', 'hash')
    