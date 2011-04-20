from django.forms import ModelForm

from oscar.core.loading import import_module

address_models = import_module('address.models', ['Country'])
order_models = import_module('order.models', ['ShippingAddress'])


class ShippingAddressForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):    
        self.fields['country'].queryset = address_models.Country._default_manager.filter(is_shipping_country=True)
    
    class Meta:
        model = order_models.ShippingAddress
        exclude = ('user',)

