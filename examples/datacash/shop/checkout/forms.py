from django.forms import ModelForm, CharField

from oscar.checkout.forms import ShippingAddressForm as CoreShippingAddressForm
from oscar.services import import_module

address_models = import_module('address.models', ['Country'])
order_models = import_module('order.models', ['ShippingAddress'])


class ShippingAddressForm(CoreShippingAddressForm):
    
    # Overriding form widgets (and labels)
    line4 = CharField(label='County')
    postcode = CharField(label='Postcode')
    
    class Meta:
        model = order_models.ShippingAddress
        exclude = ('title', 'user', 'notes', 'country')
        
    def set_country_queryset(self):
        pass

