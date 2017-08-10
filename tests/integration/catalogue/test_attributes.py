from datetime import datetime, date
import six

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from oscar.test import factories


class TestBooleanAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="boolean")

    def test_validate_boolean_values(self):
        self.assertIsNone(self.attr.validate_value(True))

    def test_validate_invalid_boolean_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestMultiOptionAttributes(TestCase):

    def setUp(self):
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ProductAttributeFactory(
            type='multi_option',
            name='Sizes',
            code='sizes',
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group)

    def test_validate_multi_option_values(self):
        self.assertIsNone(self.attr.validate_value([
            self.options[0], self.options[1]]))

    def test_validate_invalid_multi_option_values(self):
        with self.assertRaises(ValidationError):
            # value must be an iterable
            self.attr.validate_value('foobar')

        with self.assertRaises(ValidationError):
            # Items must all be AttributeOption objects
            self.attr.validate_value([self.options[0], 'notanOption'])

    def test_save_multi_option_value(self):
        product = factories.ProductFactory()
        # We'll save two out of the three available options
        self.attr.save_value(product, [self.options[0], self.options[2]])
        product.refresh_from_db()
        self.assertEqual(list(product.attr.sizes), [self.options[0], self.options[2]])

    def test_delete_multi_option_value(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, [self.options[0], self.options[1]])
        # Now delete these values
        self.attr.save_value(product, None)
        product.refresh_from_db()
        self.assertFalse(hasattr(product.attr, 'sizes'))

    def test_multi_option_value_as_text(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, self.options)
        attr_val = product.attribute_values.get(attribute=self.attr)
        self.assertEqual(attr_val.value_as_text, ", ".join(o.option for o in self.options))


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
        self.assertIsNone(self.attr.validate_value('1'))

    def test_validate_invalid_integer_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value('notanInteger')


class TestFloatAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="float")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_float_values(self):
        self.assertIsNone(self.attr.validate_value(1.2))

    def test_validate_str_float_values(self):
        self.assertIsNone(self.attr.validate_value('1.2'))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value('notaFloat')


class TestTextAttributes(TestCase):

    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="text")

    def test_validate_string_and_unicode_values(self):
        self.assertIsNone(self.attr.validate_value('String'))
        if six.PY2:
            self.assertIsNone(self.attr.validate_value(unicode('ascii_unicode', 'ascii'))) # noqa F821
            self.assertIsNone(self.attr.validate_value(unicode('utf-8_unicode', 'utf-8'))) # noqa F821

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestFileAttributes(TestCase):
    def setUp(self):
        self.attr = factories.ProductAttributeFactory(type="file")

    def test_validate_file_values(self):
        file_field = SimpleUploadedFile('test_file.txt', b'Test')
        self.assertIsNone(self.attr.validate_value(file_field))
