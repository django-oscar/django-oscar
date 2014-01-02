from django.test import TestCase
from oscar.test.factories import create_product
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _

from oscar.apps.offer import custom


class CustomRange(object):
    name = "Custom range"

    def contains_product(self, product):
        return product.title.startswith("A")

    def num_products(self):
        return None


class CustomRangeLazy(object):
    name = _("Custom range with ugettext_lazy")

    def contains_product(self, product):
        return product.title.startswith("B")

    def num_products(self):
        return None


class TestACustomRange(TestCase):

    def setUp(self):
        self.rng = custom.create_range(CustomRange)

    def test_creating_unique_custom_range(self):
        try:
            custom.create_range(CustomRange)
        except IntegrityError:
            self.fail(
                'IntegrityError when added the same CustomRange as existing')

    def test_ugettext_in_custom_range_name(self):
        try:
            custom.create_range(CustomRangeLazy)
        except Exception:
        # Here is InterfaceError in sqlite3.
        # But no InterfaceError cover in Django 1.5
            self.fail(
                'InterfaceError when added CustomRange with ugettext_lazy in name')

    def test_correctly_includes_match(self):
        test_product = create_product(title=u"A tale")
        self.assertTrue(self.rng.contains_product(test_product))

    def test_correctly_excludes_nonmatch(self):
        test_product = create_product(title=u"B tale")
        self.assertFalse(self.rng.contains_product(test_product))
