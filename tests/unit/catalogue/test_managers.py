import pytest

from django.test import TestCase

from oscar.apps.catalogue.models import Product
from oscar.test.factories import ProductFactory, ProductAttributeValueFactory


@pytest.mark.django_db
def test_public_queryset_method_filters():
    ProductFactory(is_public=True)
    ProductFactory(is_public=False)
    assert Product.objects.public().count() == 1


class ProductQuerysetPrefetchTestCase(TestCase):
    def test_get_public_children_prefetch(self):
        # Create 10 parents and 10 children for each parent.
        for _ in range(10):
            parent = ProductFactory(structure="parent", stockrecords=[])
            for _ in range(10):
                ProductFactory(structure="child", parent=parent, stockrecords=[])

        # Without prefetching, this would result in 11 queries.
        # (1) - for getting the parents
        # (10) - for each parent's children lookup.
        with self.assertNumQueries(11):
            parents = Product.objects.filter(structure="parent")
            for parent in parents:
                list(parent.get_public_children())

        # With prefetching, this should result in 2 queries.
        # (1) - for getting the parents
        # (1) - for each parent's children lookup
        with self.assertNumQueries(2):
            parents = Product.objects.filter(
                structure="parent"
            ).prefetch_public_children()
            for parent in parents:
                list(parent.get_public_children())

    def test_get_browsable_categories_prefetch(self):
        # Create 10 parents and 10 children for each parent.
        for _ in range(10):
            parent = ProductFactory(structure="parent", stockrecords=[])
            for _ in range(10):
                ProductFactory(structure="child", parent=parent, stockrecords=[])

        # Without prefetching, it would do an insane amount of queries (211)!!.
        # (1) - To get all the products (10 parents, with each 10 children = 110)
        # (10) For the parents, to get the it's own categories
        # (100) For the children, to get the parent
        # (100) For the children, to get the parent's categories
        with self.assertNumQueries(211):
            products = Product.objects.all()
            for product in products:
                list(product.get_categories())

        # With prefetching, this should result in 4 queries total.
        # (1) - To get all the products (10 parents, with each 10 children = 110)
        # (1) - To get the categories for the products itself
        # (1) - To get the parent for the childs
        # (1) - To get the categories from the parents
        with self.assertNumQueries(4):
            products = Product.objects.prefetch_browsable_categories()
            for product in products:
                list(product.get_categories())

    def test_get_attribute_values_prefetch(self):
        # Create 5 parents, each with 5 children, and give each product 3 attribute values
        for _ in range(5):
            parent = ProductFactory(structure="parent", stockrecords=[])
            for _ in range(3):
                ProductAttributeValueFactory(product=parent)
            for _ in range(5):
                child = ProductFactory(
                    structure="child", parent=parent, stockrecords=[]
                )
                for _ in range(3):
                    ProductAttributeValueFactory(product=child)

        # Without prefetching, this would result in many queries
        # (1) - for getting all products
        # (30) - for getting attribute values for each product (5 parents + 25 children)
        # (25) - for getting the parent of each child product
        with self.assertNumQueries(56):
            products = Product.objects.all()
            for product in products:
                list(product.get_attribute_values())

        # With prefetching, this should result in just 4 queries
        # (1) - for getting all products with their attribute values
        # (1) - for getting all the value_multi_option (m2m relation)
        # (1) - for getting all the attribute values for the product itself
        # (1) - for getting all the attribute values for the parent product
        # (1) - To get the attributes from the product class
        # (1) - To get the attribute from the parents' product class
        with self.assertNumQueries(6):
            products = Product.objects.prefetch_attribute_values()
            for product in products:
                list(product.get_attribute_values())

        # Verify that the prefetched data is correct
        prefetched_products = list(Product.objects.prefetch_attribute_values())
        for product in prefetched_products:
            if product.is_child:
                # Check that child products have both their own and their parent's attribute values
                child_attr_codes = set(
                    av.attribute.code for av in product.attribute_values.all()
                )
                parent_attr_codes = set(
                    av.attribute.code for av in product.parent.attribute_values.all()
                )
                prefetched_attr_codes = set(
                    av.attribute.code for av in product.get_attribute_values()
                )
                self.assertEqual(
                    prefetched_attr_codes, child_attr_codes.union(parent_attr_codes)
                )
            else:
                # Check that parent products have only their own attribute values
                own_attr_codes = set(
                    av.attribute.code for av in product.attribute_values.all()
                )
                prefetched_attr_codes = set(
                    av.attribute.code for av in product.get_attribute_values()
                )
                self.assertEqual(prefetched_attr_codes, own_attr_codes)

    def test_get_attribute_values_prefetch_including_child_attributes(self):
        # Create 5 parents, each with 5 children, and give each product 3 attribute values
        for _ in range(5):
            parent = ProductFactory(structure="parent", stockrecords=[])
            for _ in range(3):
                ProductAttributeValueFactory(product=parent)
            for _ in range(5):
                child = ProductFactory(
                    structure="child", parent=parent, stockrecords=[]
                )
                for _ in range(3):
                    ProductAttributeValueFactory(product=child)

        # Without prefetching, this would result in many queries
        # (1) - for getting all products
        # (30) - for getting attribute values for each product (5 parents + 25 children)
        # (25) - for getting the parent of each child product
        # (25) - for getting parent attribute values for each child
        # (5) - For getting the attribute values for the parent of the child, it's only 5 queries
        # because Django is smart enough to recognize the same query, and thus it's in the cache later
        with self.assertNumQueries(86):
            products = Product.objects.all()

            for product in products:
                list(product.get_attribute_values())
                if product.is_parent:
                    for child in product.children.all():
                        list(child.get_attribute_values())

        # With prefetching, but not yet including the child attributes, it's less queries, but still quite
        # a few as it will need to do a query for each child product's attribute values.
        # (1) - for getting all products with their attribute values
        # (1) - for getting all the value_multi_option (m2m relation)
        # (1) - for getting all the attribute values for the product itself
        # (1) - for getting all the attribute values for the parent product
        # (1) - To get the attributes from the product class
        # (1) - To get the attribute from the parents' product class
        # (30) - 5 for getting the parent of the children (again, django is smart enough to cache this),
        # + 25 for getting the attribute values for the children (including the parent's attribute values)
        with self.assertNumQueries(36):
            products = Product.objects.prefetch_attribute_values()

            for product in products:
                list(product.get_attribute_values())
                if product.is_parent:
                    for child in product.children.all():
                        list(child.get_attribute_values())

        # With prefetching, including the child attributes, it should result in just 8 queries
        # (1) - for getting all products with their attribute values
        # (1) - for getting all the value_multi_option (m2m relation)
        # (1) - for getting all the attribute values for the product itself
        # (1) - for getting all the attribute values for the parent product
        # (1) - To get the attributes from the product class
        # (1) - To get the attribute from the parents' product class
        # (1) - for getting the children of the parents
        # (1) - for getting all the attribute values for the child
        # (1) - for getting all the attribute values for the parent of the child
        # (1) - for getting all the value_multi_option for the parent of the child
        with self.assertNumQueries(10):
            products = Product.objects.prefetch_attribute_values(
                include_parent_children_attributes=True
            )

            for product in products:
                list(product.get_attribute_values())
                if product.is_parent:
                    for child in product.children.all():
                        list(child.get_attribute_values())

        # Verify that the prefetched data is correct
        prefetched_products = list(
            Product.objects.prefetch_attribute_values(
                include_parent_children_attributes=True
            )
        )
        for product in prefetched_products:
            if product.is_child:
                # Check that child products have both their own and their parent's attribute values
                child_attr_codes = set(
                    av.attribute.code for av in product.attribute_values.all()
                )
                parent_attr_codes = set(
                    av.attribute.code for av in product.parent.attribute_values.all()
                )
                prefetched_attr_codes = set(
                    av.attribute.code for av in product.get_attribute_values()
                )
                self.assertEqual(
                    prefetched_attr_codes, child_attr_codes.union(parent_attr_codes)
                )

                # Check that child products have the attribute values of their parent
                self.assertEqual(
                    prefetched_attr_codes, child_attr_codes.union(parent_attr_codes)
                )
            else:
                # Check that parent products have only their own attribute values
                own_attr_codes = set(
                    av.attribute.code for av in product.attribute_values.all()
                )
                prefetched_attr_codes = set(
                    av.attribute.code for av in product.get_attribute_values()
                )
                self.assertEqual(prefetched_attr_codes, own_attr_codes)

                if product.is_parent:
                    # Check that parent products have the attribute values of their children
                    for child in product.children.all():
                        child_attr_codes = set(
                            av.attribute.code for av in child.attribute_values.all()
                        )
                        combined_attr_codes = set(
                            av.attribute.code for av in product.get_attribute_values()
                        )
                        self.assertEqual(
                            combined_attr_codes, own_attr_codes.union(child_attr_codes)
                        )
