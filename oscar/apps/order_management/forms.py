from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from oscar.core.loading import import_module


class SimpleSearch(forms.Form):
    
    CHOICES=(('shipping_address', 'Shipping address'),
             ('billing_address', 'Billing address'), ('customer', 'Customer'))
    
    search_query = forms.CharField(max_length=64, label="Search for", required=True)
    search_by = forms.MultipleChoiceField(label="Using", choices=CHOICES, widget=CheckboxSelectMultiple(), required=False)
