from django.test import TestCase

from oscar.apps.offer import models
from oscar.apps.catalogue import models as catalogue_models
from oscar.test.factories import create_product


class TestWholeSiteRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)
        self.prod = create_product()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.prod))

    def test_all_products_excludes_child_products(self):
        child_product = create_product(structure='child', parent=self.prod)
        self.assertTrue(child_product not in self.range.all_products())

    def test_whitelisting(self):
        self.range.add_product(self.prod)
        self.assertTrue(self.range.contains_product(self.prod))

    def test_blacklisting(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))


class TestChildRange(TestCase):

    def setUp(self):
        self.range = models.Range.objects.create(
            name='Child-specific range', includes_all_products=False)
        self.parent = create_product(structure='parent')
        self.child1 = create_product(structure='child', parent=self.parent)
        self.child2 = create_product(structure='child', parent=self.parent)
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

    def test_included_class_with_exception(self):
        self.range.classes.add(self.parent.get_product_class())
        self.range.excluded_products.add(self.parent)
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))

    def test_included_excluded_products_in_all_products(self):
        count = 5
        included_products = [create_product() for _ in range(count)]
        excluded_products = [create_product() for _ in range(count)]

        for product in included_products:
            models.RangeProduct.objects.create(
                product=product, range=self.range)

        self.range.excluded_products.add(*excluded_products)

        all_products = self.range.all_products()
        self.assertEqual(all_products.count(), count)
        self.assertEqual(self.range.num_products(), count)

        for product in included_products:
            self.assertTrue(product in all_products)

        for product in excluded_products:
            self.assertTrue(product not in all_products)

    def test_product_classes_in_all_products(self):
        product_in_included_class = create_product(product_class="123")
        included_product_class = product_in_included_class.product_class
        excluded_product_in_included_class = create_product(
            product_class=included_product_class.name)

        self.range.classes.add(included_product_class)
        self.range.excluded_products.add(excluded_product_in_included_class)

        all_products = self.range.all_products()
        self.assertTrue(product_in_included_class in all_products)
        self.assertTrue(excluded_product_in_included_class not in
                        all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_categories_in_all_products(self):
        included_category = catalogue_models.Category.add_root(name="root")
        product_in_included_category = create_product()
        excluded_product_in_included_category = create_product()

        catalogue_models.ProductCategory.objects.create(
            product=product_in_included_category, category=included_category)
        catalogue_models.ProductCategory.objects.create(
            product=excluded_product_in_included_category,
            category=included_category)

        self.range.included_categories.add(included_category)
        self.range.excluded_products.add(excluded_product_in_included_category)

        all_products = self.range.all_products()
        self.assertTrue(product_in_included_category in all_products)
        self.assertTrue(excluded_product_in_included_category not in
                        all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_descendant_categories_in_all_products(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")

        c_product = create_product()
        gc_product = create_product()

        catalogue_models.ProductCategory.objects.create(
            product=c_product, category=child_category)
        catalogue_models.ProductCategory.objects.create(
            product=gc_product, category=grand_child_category)

        self.range.included_categories.add(parent_category)

        all_products = self.range.all_products()
        self.assertTrue(c_product in all_products)
        self.assertTrue(gc_product in all_products)

        self.assertEqual(self.range.num_products(), 2)

    def test_product_duplicated_in_all_products(self):
        """Making sure product is not duplicated in range products if it has multiple categories assigned."""

        included_category1 = catalogue_models.Category.add_root(name="cat1")
        included_category2 = catalogue_models.Category.add_root(name="cat2")
        product = create_product()
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category1)
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category2)

        self.range.included_categories.add(included_category1)
        self.range.included_categories.add(included_category2)
        self.range.add_product(product)

        all_product_ids = list(self.range.all_products().values_list('id', flat=True))
        product_occurances_in_range = all_product_ids.count(product.id)
        self.assertEqual(product_occurances_in_range, 1)

    def test_product_remove_from_range(self):
        included_category = catalogue_models.Category.add_root(name="root")
        product = create_product()
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category)

        self.range.included_categories.add(included_category)
        self.range.add_product(product)

        all_products = self.range.all_products()
        self.assertTrue(product in all_products)

        self.range.remove_product(product)

        all_products = self.range.all_products()
        self.assertFalse(product in all_products)

        # Re-adding product should return it to the products range
        self.range.add_product(product)

        all_products = self.range.all_products()
        self.assertTrue(product in all_products)

    def test_range_is_reordable(self):
        product = create_product()
        self.range.add_product(product)
        self.assertTrue(self.range.is_reorderable)

        included_category = catalogue_models.Category.add_root(name="root")
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category)
        self.range.included_categories.add(included_category)

        self.range.invalidate_cached_ids()
        self.assertFalse(self.range.is_reorderable)

        self.range.included_categories.remove(included_category)
        self.range.invalidate_cached_ids()
        self.assertTrue(self.range.is_reorderable)


class TestRangeModel(TestCase):

    def test_ensures_unique_slugs_are_used(self):
        first_range = models.Range.objects.create(name="Foo")
        first_range.name = "Bar"
        first_range.save()
        models.Range.objects.create(name="Foo")
