# -*- coding: utf-8 -*-
from django.forms import ModelForm

from oscar.core.loading import import_module
import_module('address.models', ['UserAddress'], locals())


class UserAddressForm(ModelForm):

    class Meta:
        model = UserAddress
        exclude = ('user', 'num_orders', 'hash')
    