from collections import defaultdict

from django import forms
from django.forms.widgets import Input
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def items_per_page_choices():
    n = settings.OSCAR_PRODUCTS_PER_PAGE
    return [(n*i, n*i) for i in (1, 2, 4)]


class SearchInput(Input):
    """
    Defining a search type widget
    """
    input_type = 'search'


class BaseSearchForm(forms.Form):
    # Use a tabindex of 1 so that users can hit tab on any page and it will
    # focus on the search widget.
    q = forms.CharField(
        label=_('Search'),
        widget=SearchInput({
            "placeholder": _('Search'),
            "tabindex": "1",
            "class": "form-control"
        }))

    items_per_page = forms.TypedChoiceField(
        required=False,
        choices=items_per_page_choices(),
        coerce=int,
        empty_value=settings.OSCAR_PRODUCTS_PER_PAGE
    )

    # Search
    RELEVANCY = "relevancy"
    NEWEST = "newest"
    POPULARITY = "popularity"

    SORT_BY_CHOICES = [
        (RELEVANCY, _("Relevancy")),
        (POPULARITY, _("Most popular")),
        (NEWEST, _("Newest")),
    ]

    # Map query params to sorting fields.
    SORT_BY_MAP = {
        NEWEST: '-date_created',
        POPULARITY: '-score'
    }

    sort_by = forms.ChoiceField(
        label=_("Sort by"), choices=[],
        widget=forms.Select(), required=False)

    def __init__(self, *args, **kwargs):
        self.selected_facets = kwargs.pop("selected_facets", [])
        super(BaseSearchForm, self).__init__(*args, **kwargs)

        self.fields['sort_by'].choices = self.SORT_BY_CHOICES

    def get_sort_params(self, clean_data):
        return self.SORT_BY_MAP.get(clean_data.get('sort_by'), None)

    @property
    def selected_multi_facets(self):
        """
        Validate and return the selected facets
        """
        # Process selected facets into a dict(field->[*values]) to handle
        # multi-faceting
        selected_multi_facets = defaultdict(list)

        for facet_kv in self.selected_facets:
            if ":" not in facet_kv:
                continue
            field_name, value = facet_kv.split(':', 1)

            # TODO only allow valid facet queries

            selected_multi_facets[field_name].append(value)

        return selected_multi_facets


class AutoSuggestForm(forms.Form):

    q = forms.CharField()
