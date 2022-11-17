from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.core.loading import get_model
from oscar.test.factories import (
    ProductAttributeFactory, ProductClassFactory, ProductFactory)

Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class ProductAttributeTest(TestCase):

    def setUp(self):
        super().setUp()

        # setup the productclass
        self.product_class = product_class = ProductClassFactory(name='Cows', slug='cows')
        self.name_attr = ProductAttributeFactory(
            type=ProductAttribute.TEXT, product_class=product_class, name="name", code="name")
        self.weight_attrs = ProductAttributeFactory(
            type=ProductAttribute.INTEGER, name="weight", code="weight", product_class=product_class)

        # create the parent product
        self.product = product = ProductFactory(
            title="I am your father", stockrecords=None, product_class=product_class, structure="parent", upc="1234")
        product.attr.weight = 3
        product.full_clean()
        product.save()

        # create the child product
        self.child_product = ProductFactory(
            parent=product, structure="child", categories=None, product_class=None,
            title="You are my father", upc="child-1234")
        self.child_product.full_clean()

    def test_update_child_with_attributes(self):
        "Attributes preseent on the parent should not be copied to the child "
        "when title of the child is modified"
        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )

    def test_update_child_attributes(self):
        "Attributes preseent on the parent should not be copied to the child "
        "when the child attributes are modified"
        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.attr.name = "Berta"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute",
        )

    def test_update_attributes_to_parent_and_child(self):
        "Attributes present on the parent should not be copied to the child "
        "ever, not even newly added attributes"
        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )
        self.product.attr.name = "Greta"
        self.product.save()
        self.product.refresh_from_db()
        self.product.attr.refresh()

        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            2,
            "The parent now has 2 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.attr.name = "Berta"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute",
        )

    def test_explicit_identical_child_attribute(self):
        self.assertEqual(self.product.attr.weight, 3, "parent product has weight 3")
        self.assertEqual(self.child_product.attr.weight, 3, "chiuld product also has weight 3")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes, which is the weight",
        )
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes, because it gets weight from the parent",
        )
        # explicitly set a value to the child
        self.child_product.attr.weight = 3
        self.child_product.full_clean()
        self.child_product.save()
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute, because we explicitly set the attribute, "
            "so it saved, even when the parent has the same value",
        )


class ProductAttributeQuerysetTest(TestCase):
    fixtures = ["productattributes"]

    def test_query_multiple_producttypes(self):
        "We should be able to query over multiple product classes"
        result = Product.objects.filter_by_attributes(henkie="bah bah")
        self.assertEqual(result.count(), 2)
        result1, result2 = list(result)

        self.assertNotEqual(result1.product_class, result2.product_class)
        self.assertEqual(result1.attr.henkie, result2.attr.henkie)

    def test_further_filtering(self):
        "The returned queryset should be ready for further filtering"
        result = Product.objects.filter_by_attributes(henkie="bah bah")
        photo = result.filter(title__contains="Photo")
        self.assertEqual(photo.count(), 1)

    def test_empty_results(self):
        "Empty results are possible without errors"
        result = Product.objects.filter_by_attributes(doesnotexist=True)
        self.assertFalse(result.exists(), "querying with bulshit attributes should give no results")
        result = Product.objects.filter_by_attributes(henkie="zulthoofd")
        self.assertFalse(result.exists(), "querying with non existing values should give no results")
        result = Product.objects.filter_by_attributes(henkie=True)
        self.assertFalse(result.exists(), "querying with wring value type should give no results")

    def test_text_value(self):
        result = Product.objects.filter_by_attributes(subtitle="superhenk")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle="kekjo")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle=True)
        self.assertFalse(result.exists())

    def test_formatted_text(self):
        html = "<p style=\"margin: 0px; font-stretch: normal; font-size: 12px; line-height: normal; font-family: Helvetica;\">Vivamus auctor leo vel dui. Aliquam erat volutpat. Phasellus nibh. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Cras tempor. Morbi egestas, <em>urna</em> non consequat tempus, <strong>nunc</strong> arcu mollis enim, eu aliquam erat nulla non nibh. Duis consectetuer malesuada velit. Nam ante nulla, interdum vel, tristique ac, condimentum non, tellus. Proin ornare feugiat nisl. Suspendisse dolor nisl, ultrices at, eleifend vel, consequat at, dolor.</p>"  # noqa
        result = Product.objects.filter_by_attributes(additional_info=html)
        self.assertTrue(result.exists())

    def test_boolean(self):
        result = Product.objects.filter_by_attributes(available=True)
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(available=0)
        self.assertTrue(result.exists())
        with self.assertRaises(ValidationError):
            result = Product.objects.filter_by_attributes(available="henk")

    def test_number(self):
        result = Product.objects.filter_by_attributes(facets=4)
        self.assertTrue(result.exists())
        with self.assertRaises(ValueError):
            result = Product.objects.filter_by_attributes(facets="four")

        result = Product.objects.filter_by_attributes(facets=1)
        self.assertFalse(result.exists())

    def test_float(self):
        result = Product.objects.filter_by_attributes(hypothenusa=1.25)
        self.assertTrue(result.exists())
        with self.assertRaises(ValueError):
            result = Product.objects.filter_by_attributes(facets="four")

        result = Product.objects.filter_by_attributes(hypothenusa=1)
        self.assertFalse(result.exists())

    def test_option(self):
        result = Product.objects.filter_by_attributes(kind="totalitarian")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(kind=True)
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(kind="omnimous")
        self.assertFalse(result.exists())

    def test_multi_option(self):
        result = Product.objects.filter_by_attributes(subkinds="megalomane")
        self.assertTrue(result.exists())
        self.assertEqual(result.count(), 2)
        result = Product.objects.filter_by_attributes(subkinds=True)
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(subkinds="omnimous")
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(subkinds__contains="om")
        self.assertTrue(result.exists(), "megalomane conains om")
        self.assertEqual(result.count(), 2)

    def test_multiple_attributes(self):
        result = Product.objects.filter_by_attributes(subkinds="megalomane", available=True)
        self.assertTrue(result.exists())

        result = Product.objects.filter_by_attributes(
            kind="totalitarian",
            hypothenusa=1.25,
            facets=8,
            subtitle="superhenk",
            subkinds="megalomane",
            available=False
        )
        self.assertTrue(result.exists())

    def test_lookups(self):
        result = Product.objects.filter_by_attributes(facets__lte=4)
        self.assertEqual(result.count(), 1)

        result = Product.objects.filter_by_attributes(facets__lte=8)
        self.assertEqual(result.count(), 2)

        result = Product.objects.filter_by_attributes(facets__lt=8)
        self.assertEqual(result.count(), 1)
