from django.test import TestCase

from oscar.apps.es_search.forms import BaseSearchForm


class BaseSearchFormTestCase(TestCase):

    def test_SORT_BY_CHOICES_is_added_to_sort_by_field_choices(self):
        search_form = BaseSearchForm()
        self.assertEqual(
            search_form.fields['sort_by'].choices,
            BaseSearchForm.SORT_BY_CHOICES
        )

    def test_get_sort_by_params_returns_defined_params_for_selected_sort_by_value(self):
        search_form = BaseSearchForm(data={'sort_by': BaseSearchForm.NEWEST})
        search_form.is_valid()

        self.assertEqual(
            search_form.get_sort_params(search_form.cleaned_data),
            BaseSearchForm.SORT_BY_MAP[BaseSearchForm.NEWEST]
        )

    def test_selected_multi_facets_returns_key_value_pairs_of_selected_facets(self):
        search_form = BaseSearchForm(selected_facets=['key:val1', 'key:val2', 'foo:bar'])

        self.assertEqual(
            search_form.selected_multi_facets,
            {
                'key': ['val1', 'val2'],
                'foo': ['bar']
            }
        )

    def test_selected_multi_facets_skips_values_not_separated_by_colon(self):
        search_form = BaseSearchForm(selected_facets=['key:val1', 'key:val2', 'foo-bar'])

        self.assertEqual(
            search_form.selected_multi_facets,
            {
                'key': ['val1', 'val2']
            }
        )
