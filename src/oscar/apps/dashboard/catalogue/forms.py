from django import forms
from django.utils.translation import ugettext_lazy as _
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

Category = get_model('catalogue', 'Category')

CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image'])


class ProductSearchForm(forms.Form):
    upc = forms.CharField(max_length=16, required=False, label=_('UPC'))
    title = forms.CharField(
        max_length=255, required=False, label=_('Product title'))

    def clean(self):
        cleaned_data = super(ProductSearchForm, self).clean()
        cleaned_data['upc'] = cleaned_data['upc'].strip()
        cleaned_data['title'] = cleaned_data['title'].strip()
        return cleaned_data


class StockAlertSearchForm(forms.Form):
    status = forms.CharField(label=_('Status'))