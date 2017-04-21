from oscar.forms import fields
from django.test import TestCase


class TestExtendedURLField(TestCase):
    """ExtendedURLField"""

    def test_validates_local_urls(self):
        field = fields.ExtendedURLField(verify_exists=True)
        field.clean('/')
