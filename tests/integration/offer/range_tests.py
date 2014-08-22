from django.test import TestCase

from oscar.apps.offer import models
from oscar.test.factories import create_product


class TestWholeSiteRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.prod = create_product()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.prod))

    def test_whitelisting(self):
        self.range.add_product(self.prod)
        self.assertTrue(self.range.contains_product(self.prod))

    def test_blacklisting(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))


class TestPartialRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=False)
        self.parent = create_product(structure='parent')
        self.child = create_product(structure='child', parent=self.parent)

    def test_empty_list(self):
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))

    def test_included_classes(self):
        self.range.classes.add(self.parent.get_product_class())
        self.assertTrue(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child))

    def test_includes(self):
        self.range.add_product(self.parent)
        self.assertTrue(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child))

    def test_cant_add_child_product(self):
        self.assertRaises(ValueError, self.range.add_product, self.child)

    def test_included_class_with_exception(self):
        self.range.classes.add(self.parent.get_product_class())
        self.range.excluded_products.add(self.parent)
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))


class TestRangeModel(TestCase):

    def test_ensures_unique_slugs_are_used(self):
        first_range = models.Range.objects.create(name="Foo")
        first_range.name = "Bar"
        first_range.save()
        models.Range.objects.create(name="Foo")
