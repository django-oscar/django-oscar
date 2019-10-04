from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")


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
