from django.test import TestCase

from oscar.forms import fields


class TestExtendedURLField(TestCase):
    """ExtendedURLField"""

    def test_validates_local_urls(self):
        field = fields.ExtendedURLField()
        field.clean("/")
