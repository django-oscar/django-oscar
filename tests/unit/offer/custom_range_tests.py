from django.test import TestCase
from oscar.test.factories import create_product

from oscar.apps.offer import custom


class CustomRange(object):
    name = "Custom range"

    def contains_product(self, product):
        return product.title.startswith("A")

    def num_products(self):
        return None


class TestACustomRange(TestCase):

    def setUp(self):
        self.rng = custom.create_range(CustomRange)

    def test_correctly_includes_match(self):
        test_product = create_product(title=u"A tale")
        self.assertTrue(self.rng.contains_product(test_product))

    def test_correctly_excludes_nonmatch(self):
        test_product = create_product(title=u"B tale")
        self.assertFalse(self.rng.contains_product(test_product))
