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


class TestCatalogueViewWithAnInvalidForm(TestCase):
    """The issue reported the crash through the catalogue view."""

    def test_invalid_sort_by_renders_the_page(self):
        response = self.client.get("/catalogue/", {"sort_by": "bogus"})

        self.assertEqual(response.status_code, 200)

    def test_invalid_sort_by_renders_the_page_for_head(self):
        response = self.client.head("/catalogue/", {"sort_by": "bogus"})

        self.assertEqual(response.status_code, 200)
