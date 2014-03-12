from django import forms
from django.forms.widgets import Input
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from haystack.forms import FacetedSearchForm


class SearchInput(Input):
    """
    Defining a search type widget

    This is an HTML5 thing and works nicely with Safari, other browsers default
    back to using the default "text" type
    """
    input_type = 'search'


class SearchForm(FacetedSearchForm):
    """
    In Haystack, the search form is used for interpretting
    and sub-filtering the SQS.
    """
    # Use a tabindex of 1 so that users can hit tab on any page and it will
    # focus on the search widget.
    q = forms.CharField(
        required=False, label=_('Search'),
        widget=SearchInput({"placeholder": _('Search'), "tabindex": "1"}))

    # Search
    RELEVANCY = "relevancy"
    NEWEST = "newest"
    PRICE_HIGH_TO_LOW = "price-desc"
    PRICE_LOW_TO_HIGH = "price-asc"
    TITLE_A_TO_Z = "title-asc"
    TITLE_Z_TO_A = "title-desc"

    SORT_BY_CHOICES = [
        (RELEVANCY, _("Relevancy")),
        (NEWEST, _("Newest")),
        (PRICE_HIGH_TO_LOW, _("Price high To low")),
        (PRICE_LOW_TO_HIGH, _("Price low To high")),
        (TITLE_A_TO_Z, _("Title A to Z")),
        (TITLE_Z_TO_A, _("Title Z to A")),
    ]

    # Map query params to sorting fields.  Note relevancy isn't included here
    # as we assume results are returned in relevancy order in the absence of an
    # explicit sort field being passed to the search backend.
    SORT_BY_MAP = {
        NEWEST: '-date_created',
        PRICE_HIGH_TO_LOW: '-price',
        PRICE_LOW_TO_HIGH: 'price',
        TITLE_A_TO_Z: 'title_s',
        TITLE_Z_TO_A: '-title_s',
    }
    # Non Solr backends don't support dynamic fields so we just sort on title
    if 'solr' not in settings.HAYSTACK_CONNECTIONS['default']['ENGINE']:
        SORT_BY_MAP[TITLE_A_TO_Z] = 'title'
        SORT_BY_MAP[TITLE_Z_TO_A] = '-title'

    sort_by = forms.ChoiceField(
        choices=SORT_BY_CHOICES, widget=forms.Select(), required=False)

    def search(self):
        # We replace the 'search' method from FacetedSearchForm, so that we can
        # handle range queries

        # Note, we call super on a parent class as the default faceted view
        # escapes everything (which doesn't work for price range queries)
        sqs = super(FacetedSearchForm, self).search()

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:
        for facet in self.selected_facets:
            if ":" not in facet:
                continue
            field, value = facet.split(":", 1)
            if value:
                if field == 'price_exact':
                    # Don't wrap value in speech marks and don't clean value
                    sqs = sqs.narrow(u'%s:%s' % (field, value))
                else:
                    sqs = sqs.narrow(u'%s:"%s"' % (
                        field, sqs.query.clean(value)))

        if self.is_valid() and 'sort_by' in self.cleaned_data:
            sort_field = self.SORT_BY_MAP.get(
                self.cleaned_data['sort_by'], None)
            if sort_field:
                sqs = sqs.order_by(sort_field)

        return sqs
