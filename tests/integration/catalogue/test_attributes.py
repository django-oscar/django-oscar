from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models


class TestProductAttributes(TestCase):

    def test_validate_boolean_values(self):
        attr = models.ProductAttribute(type="boolean")
        with self.assertRaises(ValidationError):
                attr.validate_value(1)
