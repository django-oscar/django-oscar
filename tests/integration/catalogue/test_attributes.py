from django.test import TestCase
from django.core.exceptions import ValidationError

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
        self.assertEqual(list(product.attr.sizes),
            [self.options[0], self.options[2]])

    def test_delete_multi_option_value(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, [self.options[0], self.options[1]])
        # Now delete these values
        self.attr.save_value(product, None)
        product.refresh_from_db()
        self.assertFalse(hasattr(product.attr, 'sizes'))
