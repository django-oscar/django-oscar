from django.test import TestCase

from oscar.apps.search import utils


class SearchUtilsTestCase(TestCase):
    def test_terms_buckets_to_values_list(self):
        buckets = [
            {
                "key": 5,
                "doc_count": 12
            },
            {
                "key": 15,
                "doc_count": 5
            },
            {
                "key": 25,
                "doc_count": 9
            }
        ]

        # should have twelve 5s, five 15s and nine 25s
        expected_results = [
            5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
            15, 15, 15, 15, 15,
            25, 25, 25, 25, 25, 25, 25, 25, 25
        ]

        self.assertEqual(utils.terms_buckets_to_values_list(buckets), expected_results)
