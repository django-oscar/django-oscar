from django.test import TestCase

from oscar.apps.catalogue import models


class ProductAttributesTest(TestCase):
    def setUp(self):
        self.product_class = models.ProductClass.objects.create(name='Test')
        models.ProductAttribute.objects.create(
            product_class=self.product_class, name='text', code='text',
            type=models.ProductAttribute.TEXT)
        models.ProductAttribute.objects.create(
            product_class=self.product_class, name='integer', code='integer',
            type=models.ProductAttribute.INTEGER)


    def test_non_set_attrs_are_none(self):
        product = models.Product(product_class=self.product_class)
        assert product.attr.text is None
        assert product.attr.integer is None

    def test_save_attributes(self):
        product = models.Product(product_class=self.product_class)
        product.attr.text = 'foobar'
        product.attr.integer = 1

        with self.assertNumQueries(5):
            product.save()

    def test_load_attributes(self):
        product = models.Product.objects.create(
            product_class=self.product_class)
        with self.assertNumQueries(2):
            product.attr._load_values()

    def test_orm_cache(self):
        product = models.Product.objects.create(
            product_class=self.product_class)

        product = (
            models.Product.objects
            .prefetch_related(
                'product_class__attributes',
                'attribute_values')
            .first())

        with self.assertNumQueries(0):
            product.attr._load_values()

        product.attr.text = 'foobar'
        with self.assertNumQueries(1):
            product.attr.save()
