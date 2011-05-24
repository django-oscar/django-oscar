from django.forms import ModelForm

from oscar.core.loading import import_module

import_module('address.models', ['Country'], locals())
import_module('order.models', ['ShippingAddress'], locals())


class ShippingAddressForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):    
        self.fields['country'].queryset = Country._default_manager.filter(is_shipping_country=True)
    
    class Meta:
        model = ShippingAddress
        exclude = ('user', 'search_text')

