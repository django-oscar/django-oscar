from django import forms
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_classes


BaseSearchForm, BaseAutoSuggestForm = get_classes('search.forms', ['BaseSearchForm', 'AutoSuggestForm'])


class CatalogueSearchForm(BaseSearchForm):
    # Search
    RELEVANCY = "relevancy"
    TOP_RATED = "rating"
    NEWEST = "newest"
    PRICE_HIGH_TO_LOW = "price-desc"
    PRICE_LOW_TO_HIGH = "price-asc"
    POPULARITY = "popularity"

    SORT_BY_CHOICES = [
        (RELEVANCY, _("Relevancy")),
        (POPULARITY, _("Most popular")),
        # (TOP_RATED, _("Customer rating")),
        # (NEWEST, _("Newest")),
        (PRICE_HIGH_TO_LOW, _("Price high to low")),
        (PRICE_LOW_TO_HIGH, _("Price low to high")),
    ]

    SORT_BY_MAP = {
        # TOP_RATED: '-rating',
        # NEWEST: '-date_created',
        POPULARITY: '-score',
        PRICE_HIGH_TO_LOW: {'stock.price': {
            'order': 'desc',
            'mode': 'min',
            'nested_path': 'stock'
        }},
        PRICE_LOW_TO_HIGH: {'stock.price': {
            'order': 'asc',
            'mode': 'min',
            'nested_path': 'stock'
        }},
    }

    category = forms.IntegerField(required=False, label=_('Category'),
                                  widget=forms.HiddenInput())
    price_min = forms.FloatField(required=False, min_value=0)
    price_max = forms.FloatField(required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        super(CatalogueSearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].required = False

    def clean(self):
        cleaned_data = super(CatalogueSearchForm, self).clean()
        # Validate price ranges
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')
        if price_min and price_max and price_min > price_max:
            raise forms.ValidationError(
                "Minimum price must exceed maximum price.")


class CatalogueAutoSuggestForm(BaseAutoSuggestForm):

    category = forms.IntegerField(required=False)
