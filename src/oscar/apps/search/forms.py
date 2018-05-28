from collections import defaultdict

from django import forms
from django.conf import settings
from django.forms.widgets import Input
from django.utils.translation import gettext_lazy as _
from haystack.forms import FacetedSearchForm

from oscar.core.loading import get_class

is_solr_supported = get_class('search.features', 'is_solr_supported')


class SearchInput(Input):
    """
    Defining a search type widget

    This is an HTML5 thing and works nicely with Safari, other browsers default
    back to using the default "text" type
    """
    input_type = 'search'


# Build a dict of valid queries
VALID_FACET_QUERIES = defaultdict(list)
for facet in settings.OSCAR_SEARCH_FACETS['queries'].values():
    field_name = "%s_exact" % facet['field']
    queries = [t[1] for t in facet['queries']]
    VALID_FACET_QUERIES[field_name].extend(queries)


class SearchForm(FacetedSearchForm):
    """
    In Haystack, the search form is used for interpreting
    and sub-filtering the SQS.
    """
    # Use a tabindex of 1 so that users can hit tab on any page and it will
    # focus on the search widget.
    q = forms.CharField(
        required=False, label=_('Search'),
        widget=SearchInput({
            "placeholder": _('Search'),
            "tabindex": "1",
            "class": "form-control"
        }))

    # Search
    RELEVANCY = "relevancy"
    TOP_RATED = "rating"
    NEWEST = "newest"
    PRICE_HIGH_TO_LOW = "price-desc"
    PRICE_LOW_TO_HIGH = "price-asc"
    TITLE_A_TO_Z = "title-asc"
    TITLE_Z_TO_A = "title-desc"

    SORT_BY_CHOICES = [
        (RELEVANCY, _("Relevancy")),
        (TOP_RATED, _("Customer rating")),
        (NEWEST, _("Newest")),
        (PRICE_HIGH_TO_LOW, _("Price high to low")),
        (PRICE_LOW_TO_HIGH, _("Price low to high")),
        (TITLE_A_TO_Z, _("Title A to Z")),
        (TITLE_Z_TO_A, _("Title Z to A")),
    ]

    # Map query params to sorting fields.  Note relevancy isn't included here
    # as we assume results are returned in relevancy order in the absence of an
    # explicit sort field being passed to the search backend.
    SORT_BY_MAP = {
        TOP_RATED: '-rating',
        NEWEST: '-date_created',
        PRICE_HIGH_TO_LOW: '-price',
        PRICE_LOW_TO_HIGH: 'price',
        TITLE_A_TO_Z: 'title_s',
        TITLE_Z_TO_A: '-title_s',
    }
    # Non Solr backends don't support dynamic fields so we just sort on title
    if not is_solr_supported():
        SORT_BY_MAP[TITLE_A_TO_Z] = 'title_exact'
        SORT_BY_MAP[TITLE_Z_TO_A] = '-title_exact'

    sort_by = forms.ChoiceField(
        label=_("Sort by"), choices=SORT_BY_CHOICES,
        widget=forms.Select(), required=False)

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

            # Validate query facets as they as passed unescaped to Solr
            if field_name in VALID_FACET_QUERIES:
                if value not in VALID_FACET_QUERIES[field_name]:
                    # Invalid query value
                    continue

            selected_multi_facets[field_name].append(value)

        return selected_multi_facets

    def search(self):
        # We replace the 'search' method from FacetedSearchForm, so that we can
        # handle range queries
        # Note, we call super on a parent class as the default faceted view
        # escapes everything (which doesn't work for price range queries)
        sqs = super(FacetedSearchForm, self).search()

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:
        for field, values in self.selected_multi_facets.items():
            if not values:
                continue
            if field in VALID_FACET_QUERIES:
                # Query facet - don't wrap value in speech marks and don't
                # clean value. Query values should have been validated by this
                # point and so we don't need to escape them.
                sqs = sqs.narrow('%s:(%s)' % (
                    field, " OR ".join(values)))
            else:
                # Field facet - clean and quote the values
                clean_values = [
                    '"%s"' % sqs.query.clean(val) for val in values]
                sqs = sqs.narrow('%s:(%s)' % (
                    field, " OR ".join(clean_values)))

        if self.is_valid() and 'sort_by' in self.cleaned_data:
            sort_field = self.SORT_BY_MAP.get(
                self.cleaned_data['sort_by'], None)
            if sort_field:
                sqs = sqs.order_by(sort_field)

        return sqs


class BrowseCategoryForm(SearchForm):
    """
    Variant of SearchForm that returns all products (instead of none) if no
    query is specified.
    """

    def no_query_found(self):
        return self.searchqueryset
