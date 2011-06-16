from django.forms import ModelForm
from django.db.models import get_model


class ShippingAddressForm(ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):    
        self.fields['country'].queryset = get_model('address', 'country')._default_manager.filter(is_shipping_country=True)
    
    class Meta:
        model = get_model('order', 'shippingaddress')
        exclude = ('user', 'search_text')

