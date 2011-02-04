from django.forms import ModelForm

from oscar.services import import_module

order_models = import_module('order.models', ['ShippingAddress'])


class ShippingAddressForm(ModelForm):
    
    class Meta:
        model = order_models.ShippingAddress
        exclude = ('user',)

