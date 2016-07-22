from django import forms
from django.utils.translation import ugettext_lazy as _
from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

ProductClass = get_model('catalogue', 'ProductClass')
Category = get_model('catalogue', 'Category')

CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image'])


class ProductClassSelectForm(forms.Form):
    """
    Form which is used before creating a product to select it's product class
    """

    product_class = forms.ModelChoiceField(
        label=_("Create a new product of type"),
        empty_label=_("-- Choose type --"),
        queryset=ProductClass.objects.all())

    def __init__(self, *args, **kwargs):
        """
        If there's only one product class, pre-select it
        """
        super(ProductClassSelectForm, self).__init__(*args, **kwargs)
        qs = self.fields['product_class'].queryset
        if not kwargs.get('initial') and len(qs) == 1:
            self.fields['product_class'].initial = qs[0]


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


class ProductClassForm(forms.ModelForm):

    class Meta:
        model = ProductClass
        fields = ['name', 'requires_shipping', 'track_stock', 'options']
