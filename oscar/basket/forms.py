from django import forms

class AddToBasketForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
