from django import forms
from django.db.models import get_model


class ShippingAddressForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):    
        self.fields['country'].queryset = get_model('address', 'country')._default_manager.filter(is_shipping_country=True)
    
    class Meta:
        model = get_model('order', 'shippingaddress')
        exclude = ('user', 'search_text')


# The BillingAddress form is in oscar.apps.payment.forms
