from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from oscar.models.fields import NullCharField


class NullCharFieldTest(TestCase):
    def test_from_db_value_converts_null_to_string(self):
        field = NullCharField()
        self.assertEqual(
            "",
            field.from_db_value(None, expression=None, connection=None, context=None),
        )

    def test_get_prep_value_converts_empty_string_to_null(self):
        field = NullCharField()
        self.assertEqual(None, field.get_prep_value(""))

    def test_raises_exception_for_invalid_null_blank_combo(self):
        with self.assertRaises(ImproperlyConfigured):
            NullCharField(null=True, blank=False)

        with self.assertRaises(ImproperlyConfigured):
            NullCharField(null=False, blank=True)

        with self.assertRaises(ImproperlyConfigured):
            NullCharField(null=False, blank=False)
