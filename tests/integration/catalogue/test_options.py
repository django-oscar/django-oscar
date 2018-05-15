from django.test import TestCase

from oscar.test import factories
from oscar.core.loading import get_model


Product = get_model('catalogue', 'Product')


class ProductOptionTests(TestCase):
    def setUp(self):
        self.product_class = factories.ProductClassFactory()
        self.product = factories.create_product(product_class=self.product_class)
        self.option = factories.OptionFactory()

    def test_product_has_options_per_product_class(self):
        self.product_class.options.add(self.option)
        self.assertTrue(self.product.has_options)

    def test_product_has_options_per_product(self):
        self.product.product_options.add(self.option)
        self.assertTrue(self.product.has_options)

    def test_queryset_per_product_class(self):
        self.product_class.options.add(self.option)
        qs = Product.browsable.base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertEquals(product.num_product_class_options, 1)

    def test_queryset_per_product(self):
        self.product.product_options.add(self.option)
        qs = Product.browsable.base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertEquals(product.num_product_options, 1)
