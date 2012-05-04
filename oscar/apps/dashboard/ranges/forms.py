import re

from django import forms
from django.db.models import get_model

Product = get_model('catalogue', 'Product')


class RangeProductForm(forms.Form):
    query = forms.CharField(max_length=1024,
                            widget=forms.Textarea,
                            help_text="""You can paste in a selection of SKUs""")

    def __init__(self, range, *args, **kwargs):
        self.range = range
        super(RangeProductForm, self).__init__(*args, **kwargs)

    def clean_query(self):
        raw = self.cleaned_data['query']

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
        return self.products

    def get_missing_skus(self):
        return self.missing_skus

    def get_duplicate_skus(self):
        return self.duplicate_skus
