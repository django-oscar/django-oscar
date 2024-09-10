import pickle
import unittest
from copy import deepcopy

from django.db import connection
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext

from oscar.core.loading import get_model
from oscar.test.factories import (
    PartnerFactory,
    ProductAttributeFactory,
    ProductClassFactory,
    ProductFactory,
)

Product = get_model("catalogue", "Product")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class ProductAttributeTest(TransactionTestCase):
    def setUp(self):
        super().setUp()

        # setup the productclass
        self.product_class = product_class = ProductClassFactory(
            name="Cows", slug="cows"
        )
        self.name_attr = ProductAttributeFactory(
            type=ProductAttribute.TEXT,
            product_class=product_class,
            name="name",
            code="name",
        )
        self.weight_attr = ProductAttributeFactory(
            type=ProductAttribute.INTEGER,
            name="weight",
            code="weight",
            product_class=product_class,
            required=True,
        )
        self.richtext_attr = ProductAttributeFactory(
            type=ProductAttribute.RICHTEXT,
            name="html",
            code="html",
            product_class=product_class,
            required=False,
        )

        # create the parent product
        self.product = product = ProductFactory(
            title="I am your father",
            stockrecords=None,
            product_class=product_class,
            structure="parent",
            upc="1234",
        )
        product.attr.weight = 3
        product.full_clean()
        product.save()

        # create the child product
        self.child_product = ProductFactory(
            parent=product,
            structure="child",
            categories=None,
            product_class=None,
            title="You are my father",
            upc="child-1234",
        )
        self.child_product.full_clean()

    def test_update_child_with_attributes(self, num_queries=11):
        """
        Attributes preseent on the parent should not be copied to the child
        when title of the child is modified
        """
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product_id=self.product.pk
                ).count(),
                1,
                "The parent has 1 attributes",
            )

            # establish baseline
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
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
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
                0,
                "The child has no attributes",
            )

            # In some django versions, the query count is a bit different because the
            # transactions aren't included in the count.
            self.assertTrue(num_queries <= len(queries) <= num_queries + 2)

    def test_update_child_with_attributes_with_prefetched_attribute_values(self):
        """
        Attributes preseent on the parent should not be copied to the child
        when title of the child is modified, even when the attribute values are prefetched.
        """
        self.product = Product.objects.prefetch_attribute_values().get(
            pk=self.product.pk
        )
        self.child_product = Product.objects.prefetch_attribute_values().get(
            pk=self.child_product.pk
        )
        self.test_update_child_with_attributes(num_queries=10)

    def test_update_child_attributes(self, num_queries=12):
        """
        Attributes preseent on the parent should not be copied to the child
        when the child attributes are modified
        """
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product_id=self.product.pk
                ).count(),
                1,
                "The parent has 1 attributes",
            )

            # establish baseline
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
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
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
                1,
                "The child now has 1 attribute",
            )

            # In some django versions, the query count is a bit different because the
            # transactions aren't included in the count.
            self.assertTrue(num_queries <= len(queries) <= num_queries + 2)

    def test_update_child_attributes_with_prefetched_attribute_values(self):
        """
        Attributes preseent on the parent should not be copied to the child
        when the child attributes are modified, even when the attribute values are prefetched.
        """
        self.product = Product.objects.prefetch_attribute_values().get(
            pk=self.product.pk
        )
        self.child_product = Product.objects.prefetch_attribute_values().get(
            pk=self.child_product.pk
        )
        self.test_update_child_attributes(num_queries=11)

    def test_update_attributes_to_parent_and_child(self, num_queries=27):
        """
        Attributes present on the parent should not be copied to the child
        ever, not even newly added attributes
        """
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product_id=self.product.pk
                ).count(),
                1,
                "The parent has 1 attributes",
            )
            self.product.attr.name = "Greta"
            self.product.save()
            self.product.refresh_from_db()
            self.product.attr.refresh()

            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product_id=self.product.pk
                ).count(),
                2,
                "The parent now has 2 attributes",
            )

            # establish baseline
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
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
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
                1,
                "The child now has 1 attribute",
            )

            # In some django versions, the query count is a bit different because the
            # transactions aren't included in the count.
            self.assertTrue(len(queries) <= num_queries + 4)

    def test_update_attributes_to_parent_and_child_with_prefetched_attribute_values(
        self,
    ):
        """
        Attributes present on the parent should not be copied to the child
        ever, not even newly added attributes, even when the attribute values are prefetched.
        """
        self.product = Product.objects.prefetch_attribute_values().get(
            pk=self.product.pk
        )
        self.child_product = Product.objects.prefetch_attribute_values().get(
            pk=self.child_product.pk
        )
        self.test_update_attributes_to_parent_and_child(num_queries=18)

    def test_explicit_identical_child_attribute(self, num_queries=15):
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.product.attr.weight, 3, "parent product has weight 3")
            self.assertEqual(
                self.child_product.attr.weight, 3, "chiuld product also has weight 3"
            )
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product_id=self.product.pk
                ).count(),
                1,
                "The parent has 1 attributes, which is the weight",
            )
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
                0,
                "The child has no attributes, because it gets weight from the parent",
            )
            # explicitly set a value to the child
            self.child_product.attr.weight = 3
            self.child_product.full_clean()
            self.child_product.save()
            self.assertEqual(
                ProductAttributeValue.objects.filter(
                    product=self.child_product
                ).count(),
                1,
                "The child now has 1 attribute, because we explicitly set the attribute, "
                "so it saved, even when the parent has the same value",
            )

            # In some django versions, the query count is a bit different because the
            # transactions aren't included in the count.
            self.assertTrue(num_queries <= len(queries) <= num_queries + 2)

    def test_explicit_identical_child_attribute_with_prefetched_attribute_values(self):
        self.product = Product.objects.prefetch_attribute_values().get(
            pk=self.product.pk
        )
        self.child_product = Product.objects.prefetch_attribute_values().get(
            pk=self.child_product.pk
        )
        self.test_explicit_identical_child_attribute(num_queries=14)

    def test_delete_attribute_value(self):
        "Attributes should be deleted when they are nulled"
        self.assertEqual(self.product.attr.weight, 3)
        self.product.attr.weight = None
        self.product.save()

        p = Product.objects.get(pk=self.product.pk)
        with self.assertRaises(AttributeError):
            p.attr.weight  # pylint: disable=pointless-statement

    def test_validate_attribute_value(self):
        self.test_delete_attribute_value()
        with self.assertRaises(ValidationError):
            self.product.attr.validate_attributes()

    def test_deepcopy(self):
        "Deepcopy should not cause a recursion error"
        deepcopy(self.product)
        deepcopy(self.child_product)

    def test_set(self):
        "Attributes should be settable from a string key"
        self.product.attr.set("weight", 101)
        self.assertEqual(self.product.attr._dirty, {"weight"})
        self.product.attr.save()

        p = Product.objects.get(pk=self.product.pk)

        self.assertEqual(p.attr.weight, 101)

    def test_set_error(self):
        "set should only accept attributes which are valid python identifiers"
        with self.assertRaises(ValidationError):
            self.product.attr.set("bina-weight", 101)

        with self.assertRaises(ValidationError):
            self.product.attr.set("8_oepla", "oegaranos")

        with self.assertRaises(ValidationError):
            self.product.attr.set("set", "validate_identifier=True")

        with self.assertRaises(ValidationError):
            self.product.attr.set("save", "raise=True")

    def test_update(self):
        "Attributes should be updateble from a dictionary"
        self.product.attr.update({"weight": 808, "name": "a banana"})
        self.assertEqual(self.product.attr._dirty, {"weight", "name"})
        self.product.attr.save()

        p = Product.objects.get(pk=self.product.pk)

        self.assertEqual(p.attr.weight, 808)
        self.assertEqual(p.attr.name, "a banana")

    def test_validate_attributes(self):
        "validate_attributes should raise ValidationError on erroneous inputs"
        self.product.attr.validate_attributes()
        self.product.attr.weight = "koe"
        with self.assertRaises(ValidationError):
            self.product.attr.validate_attributes()

    def test_get_attribute_by_code(self):
        at = self.product.attr.get_attribute_by_code("weight")
        self.assertEqual(at.code, "weight")
        self.assertEqual(at.product_class, self.product.get_product_class())

        self.assertIsNone(self.product.attr.get_attribute_by_code("stoubafluppie"))

    def test_attribute_html(self):
        self.product.attr.html = "<h1>Hi</h1>"
        self.product.save()

        value = self.product.attr.get_value_by_attribute(self.richtext_attr)
        html = value.value_as_html
        self.assertEqual(html, "<h1>Hi</h1>")
        self.assertTrue(hasattr(html, "__html__"))

    def test_entity_attributes(self):
        unrelated_object = PartnerFactory()
        _ = ProductAttributeFactory(
            type="entity",
            product_class=self.product_class,
            name="entity",
            code="entity",
        )
        self.product.attr.entity = unrelated_object
        self.product.attr.weight = 3
        self.product.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.attr.entity, unrelated_object)

        another_product = ProductFactory(
            title="Aother",
            stockrecords=None,
            product_class=self.product_class,
            structure="standalone",
            upc="henk1239",
        )

        self.product.attr.entity = another_product
        self.product.attr.weight = 5
        self.product.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.attr.entity, another_product)

        self.product.attr.entity = None
        self.product.save()

        self.product.refresh_from_db()

        self.assertEqual(self.product.attr.entity, None)

        product = Product.objects.get(pk=self.product.pk)
        with self.assertRaises(AttributeError):
            # pylint: disable=pointless-statement
            product.attr.entity

    def test_can_be_pickled_when_initialized(self):
        """Should be able to pickle and unpickle an initialized ProductAttributesContainer"""
        product = Product.objects.get(pk=self.product.pk)

        self.assertEqual(product.attr.weight, 3)
        self.assertTrue(product.attr.initialized)

        pickled_attrs = pickle.dumps(product.attr)
        attrs = pickle.loads(pickled_attrs)

        self.assertTrue(attrs.initialized)
        self.assertEqual(attrs.weight, 3)

    def test_can_be_pickled_when_not_initialized(self):
        """Should be able to pickle and unpickle an uninitialized ProductAttributesContainer"""
        product = Product.objects.get(pk=self.product.pk)

        self.assertFalse(product.attr.initialized)

        pickled_attrs = pickle.dumps(product.attr)
        attrs = pickle.loads(pickled_attrs)

        self.assertFalse(attrs.initialized)
        self.assertEqual(attrs.weight, 3)


class MultiOptionTest(TestCase):
    fixtures = ["productattributes"]
    maxDiff = None

    def test_multi_option_recursion_error(self):
        product = Product.objects.get(pk=4)
        with self.assertRaises(ValueError):
            product.attr.set("subkinds", "harrie")
            product.save()

    def test_value_as_html(self):
        product = Product.objects.get(pk=4)
        # pylint: disable=unused-variable
        (
            additional_info,
            available,
            facets,
            hypothenusa,
            kind,
            releasedate,
            starttime,
            subkinds,
            subtitle,
        ) = product.attr.get_values().order_by("id")

        self.assertTrue(
            additional_info.value_as_html.startswith(
                '<p style="margin: 0px; font-stretch: normal; font-size: 12px;'
            )
        )
        self.assertEqual(available.value_as_html, "Yes")
        self.assertEqual(kind.value_as_html, "bombastic")
        self.assertEqual(subkinds.value_as_html, "grand, verocious, megalomane")
        self.assertEqual(subtitle.value_as_html, "kekjo")

    @unittest.skip("The implementation is wrong, which makes these tests fail")
    def test_broken_value_as_html(self):
        product = Product.objects.get(pk=4)
        # pylint: disable=unused-variable
        (
            additional_info,
            available,
            facets,
            hypothenusa,
            kind,
            releasedate,
            starttime,
            subkinds,
            subtitle,
        ) = product.attr.get_values().order_by("id")

        self.assertEqual(starttime.value_as_html, "2018-11-16T09:15:00+00:00")
        self.assertEqual(facets.value_as_html, "4")
        self.assertEqual(releasedate.value_as_html, "2018-11-16")
        self.assertEqual(hypothenusa.value_as_html, "2.4567")


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
        self.assertFalse(
            result.exists(), "querying with bulshit attributes should give no results"
        )
        result = Product.objects.filter_by_attributes(henkie="zulthoofd")
        self.assertFalse(
            result.exists(), "querying with non existing values should give no results"
        )
        result = Product.objects.filter_by_attributes(henkie=True)
        self.assertFalse(
            result.exists(), "querying with wring value type should give no results"
        )

    def test_text_value(self):
        result = Product.objects.filter_by_attributes(subtitle="superhenk")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle="kekjo")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle=True)
        self.assertFalse(result.exists())

    def test_formatted_text(self):
        html = '<p style="margin: 0px; font-stretch: normal; font-size: 12px; line-height: normal; font-family: Helvetica;">Vivamus auctor leo vel dui. Aliquam erat volutpat. Phasellus nibh. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Cras tempor. Morbi egestas, <em>urna</em> non consequat tempus, <strong>nunc</strong> arcu mollis enim, eu aliquam erat nulla non nibh. Duis consectetuer malesuada velit. Nam ante nulla, interdum vel, tristique ac, condimentum non, tellus. Proin ornare feugiat nisl. Suspendisse dolor nisl, ultrices at, eleifend vel, consequat at, dolor.</p>'  # noqa
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
        result = Product.objects.filter_by_attributes(
            subkinds="megalomane", available=True
        )
        self.assertTrue(result.exists())

        result = Product.objects.filter_by_attributes(
            kind="totalitarian",
            hypothenusa=1.25,
            facets=8,
            subtitle="superhenk",
            subkinds="megalomane",
            available=False,
        )
        self.assertTrue(result.exists())

    def test_lookups(self):
        result = Product.objects.filter_by_attributes(facets__lte=4)
        self.assertEqual(result.count(), 1)

        result = Product.objects.filter_by_attributes(facets__lte=8)
        self.assertEqual(result.count(), 2)

        result = Product.objects.filter_by_attributes(facets__lt=8)
        self.assertEqual(result.count(), 1)
