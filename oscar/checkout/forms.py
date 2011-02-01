from django.forms import ModelForm

from oscar.services import import_module

order_models = import_module('order.models', ['DeliveryAddress'])


class DeliveryAddressForm(ModelForm):
    
    class Meta:
        model = order_models.DeliveryAddress
        exclude = ('user',)
