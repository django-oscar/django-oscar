from django import forms

from oscar.services import import_module

payment_models = import_module('payment.models', ['Bankcard'])


class BankcardForm(forms.ModelForm):
    
    class Meta:
        model = payment_models.Bankcard
        exclude = ('user', 'partner_reference')
    