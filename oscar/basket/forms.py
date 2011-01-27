from django import forms

class AddToBasketForm(forms.Form):
    action = forms.CharField(widget=forms.HiddenInput(), initial='add')
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1)
