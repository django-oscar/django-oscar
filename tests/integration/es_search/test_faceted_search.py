from django.test import TestCase

from oscar.apps.es_search.faceted_search import AutoRangeFacet


class AutoRangeFacetTestCase(TestCase):

    def test_size_param_added_in_init(self):
        facet = AutoRangeFacet(group_count=1)
        self.assertEqual(
            facet._params['size'],
            AutoRangeFacet.RESULT_SIZE
        )
