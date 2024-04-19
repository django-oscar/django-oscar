from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from oscar.apps.catalogue.models import Product, ProductAttribute, ProductClass
from oscar.test import factories


class TestContainer(TestCase):
    def test_attributes_initialised_before_write(self):
        # Regression test for https://github.com/django-oscar/django-oscar/issues/3258
        product_class = factories.ProductClassFactory()
        product_class.attributes.create(name="a1", code="a1", required=True)
        product_class.attributes.create(name="a2", code="a2", required=False)
        product_class.attributes.create(name="a3", code="a3", required=True)
        product = factories.ProductFactory(product_class=product_class)
        product.attr.a1 = "v1"
        product.attr.a3 = "v3"
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        product.attr.a1 = "v2"
        product.attr.a3 = "v6"
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        assert product.attr.a1 == "v2"
        assert product.attr.a3 == "v6"

    def test_attributes_refresh(self):
        product_class = factories.ProductClassFactory()
        product_class.attributes.create(name="a1", code="a1", required=True)
        product = factories.ProductFactory(product_class=product_class)
        product.attr.a1 = "v1"
        product.attr.save()

        product_attr = ProductAttribute.objects.get(code="a1", product=product)
        product_attr.save_value(product, "v2")
        assert product.attr.a1 == "v1"

        product.attr.refresh()
        assert product.attr.a1 == "v2"

    def test_attribute_code_uniqueness(self):
        product_class = factories.ProductClassFactory()
        attribute1 = ProductAttribute.objects.create(
            name="a1", code="a1", product_class=product_class
        )
        attribute1.full_clean()

        with self.assertRaises(ValidationError):
            ProductAttribute(
                name="a1", code="a1", product_class=product_class
            ).full_clean()

        another_product_class = ProductClass.objects.create(
            name="another product class"
        )
        ProductAttribute(
            name="a1", code="a1", product_class=another_product_class
        ).full_clean()


class TestBooleanAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="boolean")

    def test_validate_boolean_values(self):
        self.assertIsNone(self.attr.validate_value(True))

    def test_validate_invalid_boolean_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)

    def test_boolean_value_as_text_true(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, True)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == "Yes"

    def test_boolean_value_as_text_false(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, False)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == "No"


class TestMultiOptionAttributes(TestCase):
    def setUp(self):
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ProductAttributeFactory(
            type="multi_option",
            name="Sizes",
            code="sizes",
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group
        )

    def test_validate_multi_option_values(self):
        self.assertIsNone(self.attr.validate_value([self.options[0], self.options[1]]))

    def test_validate_invalid_multi_option_values(self):
        with self.assertRaises(ValidationError):
            # value must be an iterable
            self.attr.validate_value("foobar")

        with self.assertRaises(ValidationError):
            # Items must all be AttributeOption objects
            self.attr.validate_value([self.options[0], "notanOption"])

    def test_save_multi_option_value(self):
        product = factories.ProductFactory()
        # We'll save two out of the three available options
        self.attr.save_value(product, [self.options[0], self.options[2]])
        product = Product.objects.get(pk=product.pk)
        self.assertEqual(list(product.attr.sizes), [self.options[0], self.options[2]])

    def test_delete_multi_option_value(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, [self.options[0], self.options[1]])
        # Now delete these values
        self.attr.save_value(product, None)
        product = Product.objects.get(pk=product.pk)
        self.assertFalse(hasattr(product.attr, "sizes"))

    def test_multi_option_value_as_text(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, self.options)
        attr_val = product.attribute_values.get(attribute=self.attr)
        self.assertEqual(
            attr_val.value_as_text, ", ".join(o.option for o in self.options)
        )


class TestOptionAttributes(TestCase):
    def setUp(self):
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ProductAttributeFactory(
            type="option",
            name="Size",
            code="size",
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group
        )

    def test_option_value_as_text(self):
        product = factories.ProductFactory()
        option_2 = self.options[1]
        self.attr.save_value(product, option_2)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == str(option_2)


class TestDatetimeAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="datetime")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_invalid_datetime_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestDateAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="date")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_date_values(self):
        self.assertIsNone(self.attr.validate_value(date.today()))

    def test_validate_invalid_date_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestIntegerAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="integer")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_str_integer_values(self):
        self.assertIsNone(self.attr.validate_value("1"))

    def test_validate_invalid_integer_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value("notanInteger")


class TestFloatAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="float")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_float_values(self):
        self.assertIsNone(self.attr.validate_value(1.2))

    def test_validate_str_float_values(self):
        self.assertIsNone(self.attr.validate_value("1.2"))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value("notaFloat")


class TestTextAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="text")

    def test_validate_string_and_unicode_values(self):
        self.assertIsNone(self.attr.validate_value("String"))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestFileAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="file", code="file")

    def test_validate_file_values(self):
        file_field = SimpleUploadedFile("test_file.txt", b"Test")
        self.assertIsNone(self.attr.validate_value(file_field))

    def test_erase_file(self):
        product = factories.ProductFactory()
        product.product_class.attributes.add(self.attr)

        # save file attribute
        file_field = SimpleUploadedFile("test_file.txt", b"Test")
        self.assertIsNone(self.attr.validate_value(file_field))
        self.attr.save_value(product, file_field)
        self.assertTrue(self.attr.is_file)

        product = Product.objects.get(pk=product.pk)

        self.assertIsNotNone(
            product.attr.file, "There should be something saved into the file attribute"
        )
        self.assertIn(
            file_field.name,
            product.attr.file.name,
            "The save file should have the correct filename",
        )

        # set file attribute to None, which does nothing
        product.attr.file = None
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        self.assertIsNotNone(
            product.attr.file,
            "There file should not be None, even though we set it to that",
        )
        self.assertIn(
            file_field.name,
            product.attr.file.name,
            "The save file should still have the correct filename",
        )

        # set file attribute to False, which will erase it
        product.attr.file = False
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        with self.assertRaises(AttributeError):
            self.assertIn(file_field.name, product.attr.file.name)
