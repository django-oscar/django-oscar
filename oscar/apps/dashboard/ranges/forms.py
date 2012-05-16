import re

from django import forms
from django.db.models import get_model

Product = get_model('catalogue', 'Product')
Range = get_model('offer', 'Range')


class RangeForm(forms.ModelForm):

    class Meta:
        model = Range
        exclude = ('included_products', 'excluded_products', 'classes')


class RangeProductForm(forms.Form):
    query = forms.CharField(max_length=1024,
                            label="Product SKUs",
                            widget=forms.Textarea,
                            required=False,
                            help_text="""You can paste in a selection of SKUs""")
    file_upload = forms.FileField(label="File of SKUs", required=False,
                                  help_text='Either comma-separated, or one SKU per line')

    def __init__(self, range, *args, **kwargs):
        self.range = range
        super(RangeProductForm, self).__init__(*args, **kwargs)

    def clean(self):
        clean_data = super(RangeProductForm, self).clean()
        if not clean_data.get('query') and not clean_data.get('file_upload'):
            raise forms.ValidationError("You must submit either a list of SKUs or a file")
        return clean_data

    def clean_query(self):
        raw = self.cleaned_data['query']
        if not raw:
            return raw

        # Check that the search matches some products
        skus = re.compile(r'[\w-]+').findall(raw)
        existing_skus = self.range.included_products.all().values_list(
            'stockrecord__partner_sku', flat=True)
        new_skus = list(set(skus) - set(existing_skus))

        if len(new_skus) == 0:
            raise forms.ValidationError(
                "The products with SKUs matching %s are already in this range" % (
                    ', '.join(skus)))

        self.products = Product._default_manager.filter(stockrecord__partner_sku__in=new_skus)
        if len(self.products) == 0:
            raise forms.ValidationError("No products exist with a SKU matching %s" % ", ".join(skus))

        found_skus = self.products.values_list('stockrecord__partner_sku', flat=True)
        self.missing_skus = set(new_skus) - set(found_skus)
        self.duplicate_skus = set(existing_skus).intersection(set(skus))

        return raw

    def get_products(self):
        return self.products if hasattr(self, 'products') else []

    def get_missing_skus(self):
        return self.missing_skus

    def get_duplicate_skus(self):
        return self.duplicate_skus
