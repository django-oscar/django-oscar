from django.test import TestCase

from oscar.apps.offer import models
from oscar.apps.catalogue import models as catalogue_models
from oscar.test import factories
from oscar.test.factories import create_product


class TestWholeSiteRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.product = factories.ParentProductFactory()
        self.child = self.product.children.get()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.product))

    def test_all_products_excludes_child_products(self):
        self.assertNotIn(self.child, self.range.all_products())

    def test_whitelisting(self):
        self.range.add_product(self.product)
        self.assertTrue(self.range.contains_product(self.product))

    def test_blacklisting(self):
        self.range.excluded_products.add(self.product)
        self.assertFalse(self.range.contains_product(self.product))


class TestChildRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name='Child-specific range', includes_all_products=False)
        self.parent = factories.ParentProductFactory(children=[])
        self.child1 = factories.ChildProductFactory(parent=self.parent)
        self.child2 = factories.ChildProductFactory(parent=self.parent)
        self.range.add_product(self.child1)

    def test_includes_child(self):
        self.assertTrue(self.range.contains_product(self.child1))

    def test_does_not_include_parent(self):
        self.assertFalse(self.range.contains_product(self.parent))

    def test_does_not_include_sibling(self):
        self.assertFalse(self.range.contains_product(self.child2))


class TestPartialRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=False)
        self.parent = factories.ParentProductFactory()
        self.child = self.parent.children.get()

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

    def test_included_class_with_exception(self):
        self.range.classes.add(self.parent.get_product_class())
        self.range.excluded_products.add(self.parent)
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))

    def test_included_excluded_products_in_all_products(self):
        count = 5
        included_products = [factories.StandaloneProductFactory() for _ in range(count)]
        excluded_products = [factories.StandaloneProductFactory() for _ in range(count)]

        for product in included_products:
            models.RangeProduct.objects.create(
                product=product, range=self.range)

        self.range.excluded_products.add(*excluded_products)

        all_products = self.range.all_products()
        self.assertEqual(all_products.count(), count)
        self.assertEqual(self.range.num_products(), count)

        for product in included_products:
            self.assertIn(product, all_products)

        for product in excluded_products:
            self.assertNotIn(product, all_products)

    def test_product_classes_in_all_products(self):
        product_in_included_class = factories.StandaloneProductFactory(product_class__name="123")
        included_product_class = product_in_included_class.product_class
        excluded_product_in_included_class = factories.StandaloneProductFactory(
            product_class=included_product_class)

        self.range.classes.add(included_product_class)
        self.range.excluded_products.add(excluded_product_in_included_class)

        all_products = self.range.all_products()
        self.assertIn(product_in_included_class, all_products)
        self.assertNotIn(excluded_product_in_included_class, all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_categories_in_all_products(self):
        included_category = catalogue_models.Category.add_root(name="root")
        product_in_included_category = factories.StandaloneProductFactory(
            categories__category=included_category)
        excluded_product_in_included_category = factories.StandaloneProductFactory(
            categories__category=included_category)

        self.range.included_categories.add(included_category)
        self.range.excluded_products.add(excluded_product_in_included_category)

        all_products = self.range.all_products()
        self.assertIn(product_in_included_category, all_products)
        self.assertNotIn(excluded_product_in_included_category, all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_descendant_categories_in_all_products(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")

        product_in_child_category = factories.StandaloneProductFactory(
            categories__category=child_category)
        product_in_grand_child_category = factories.StandaloneProductFactory(
            categories__category=grand_child_category)

        self.range.included_categories.add(parent_category)

        all_products = self.range.all_products()
        self.assertIn(product_in_child_category, all_products)
        self.assertIn(product_in_grand_child_category, all_products)

        self.assertEqual(self.range.num_products(), 2)


class TestRangeModel(TestCase):

    def test_ensures_unique_slugs_are_used(self):
        first_range = models.Range.objects.create(name="Foo")
        first_range.name = "Bar"
        first_range.save()
        models.Range.objects.create(name="Foo")
