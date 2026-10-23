from unittest.mock import MagicMock, patch

from django.test import TestCase


class TestSearchViewWithAnInvalidForm(TestCase):
    """An invalid search form must render a page instead of raising."""

    def test_invalid_sort_by_renders_the_page(self):
        response = self.client.get("/search/", {"q": "anything", "sort_by": "bogus"})

        self.assertEqual(response.status_code, 200)

    def test_invalid_sort_by_renders_the_page_with_spelling_enabled(self):
        # An invalid form leaves the suggestion undefined; the view must not
        # look the query up in a context that has no query.
        queryset = MagicMock()
        queryset.query.backend.include_spelling = True
        queryset.facet_counts.return_value = {}

        with patch("oscar.apps.search.views.base.base_sqs", return_value=queryset):
            response = self.client.get(
                "/search/", {"q": "anything", "sort_by": "bogus"}
            )

        self.assertEqual(response.status_code, 200)

    def test_valid_form_renders_the_page(self):
        response = self.client.get("/search/", {"q": "anything"})

        self.assertEqual(response.status_code, 200)


class TestSearchViewSuggestion(TestCase):
    """Regression test for https://github.com/django-oscar/django-oscar/issues/4483"""

    def test_suggestion_falls_back_to_the_searched_queryset(self):
        # Solr only spellchecks the query that actually ran, so the form's own
        # (unsearched) queryset offers nothing.  The suggestion is already on
        # the queryset the view searched.
        base = MagicMock()
        base.query.backend.include_spelling = True
        base.facet_counts.return_value = {}
        base.spelling_suggestion.return_value = None

        searched = MagicMock()
        searched.query.backend.include_spelling = True
        searched.facet_counts.return_value = {}
        searched.spelling_suggestion.return_value = "blood"
        searched.load_all.return_value = searched
        searched.count.return_value = 0

        base.auto_query.return_value = searched

        with patch("oscar.apps.search.views.base.base_sqs", return_value=base):
            response = self.client.get("/search/", {"q": "bloos"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["suggestion"], "blood")


class TestCatalogueViewWithAnInvalidForm(TestCase):
    """The issue reported the crash through the catalogue view."""

    def test_invalid_sort_by_renders_the_page(self):
        response = self.client.get("/catalogue/", {"sort_by": "bogus"})

        self.assertEqual(response.status_code, 200)

    def test_invalid_sort_by_renders_the_page_for_head(self):
        response = self.client.head("/catalogue/", {"sort_by": "bogus"})

        self.assertEqual(response.status_code, 200)
