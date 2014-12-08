from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models


class TestProductOptions(TestCase):

    def test_validate_boolean_values(self):
        opt = models.Option(type="boolean")
        with self.assertRaises(ValidationError):
                opt.validate_value(1)
