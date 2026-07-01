from django.test import TestCase

from oscar.core.loading import get_model
from oscar.test import factories

Product = get_model("catalogue", "Product")


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
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertTrue(product.has_product_class_options)

    def test_queryset_per_product(self):
        self.product.product_options.add(self.option)
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertTrue(product.has_product_options, 1)

    def test_queryset_both(self):
        """
        The options attribute on a product should return a queryset containing
        both the product class options and any extra options defined on the
        product
        """

        # set up the options on product and product_class
        self.test_product_has_options_per_product_class()
        self.test_product_has_options_per_product()
        self.assertTrue(self.product.has_options, "Options should be present")
        self.assertEqual(
            self.product.options.count(),
            1,
            "options attribute should not contain duplicates",
        )
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(
            product.has_product_class_options,
            "has_product_class_options should indicate the product_class option",
        )
        self.assertTrue(
            product.has_product_options,
            "has_product_options should indicate the number of product options",
        )
        self.product_class.options.add(factories.OptionFactory(code="henk"))
        self.assertEqual(
            self.product.options.count(),
            2,
            "New product_class options should be immediately visible",
        )
        self.product.product_options.add(factories.OptionFactory(code="klaas"))
        self.assertEqual(
            self.product.options.count(),
            3,
            "New product options should be immediately visible",
        )
