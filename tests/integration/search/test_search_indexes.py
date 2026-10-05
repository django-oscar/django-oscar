from django.test import TestCase
from haystack import connections

from oscar.apps.search.facets import base_sqs


class TestProductClassFacet(TestCase):
    def test_product_class_is_faceted_on_an_untokenized_field(self):
        unified_index = connections["default"].get_unified_index()

        self.assertEqual(
            unified_index.get_facet_fieldname("product_class"), "product_class_exact"
        )
        self.assertIn("product_class_exact", base_sqs().query.facets)
