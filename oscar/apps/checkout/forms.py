from django import forms
from django.db.models import get_model
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _


class ShippingAddressForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm,self ).__init__(*args, **kwargs)
        self.set_country_queryset() 
        
    def set_country_queryset(self):
        self.fields['country'].queryset = get_model('address', 'country')._default_manager.filter(
            is_shipping_country=True)
    
    class Meta:
        model = get_model('order', 'shippingaddress')
        exclude = ('user', 'search_text')


class GatewayForm(AuthenticationForm):
    username = forms.EmailField(label=_("My email address is"))
    NEW, EXISTING = 'new', 'existing'
    CHOICES = ((NEW, _('No, I am a new customer')),
               (EXISTING, _('Yes, I have a password')))
    options = forms.ChoiceField(widget=forms.widgets.RadioSelect,
                                choices=CHOICES)

    def clean(self):
        cleaned_data = self.cleaned_data
        if self.is_guest_checkout():
            if 'password' in self.errors:
                del self.errors['password']
            return cleaned_data
        return super(GatewayForm, self).clean()

    def is_guest_checkout(self):
        return self.cleaned_data.get('options', None) == self.NEW


# The BillingAddress form is in oscar.apps.payment.forms
