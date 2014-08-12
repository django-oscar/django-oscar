from django.core.exceptions import ValidationError
from django.test import TestCase
from oscar.test.factories import create_product
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

    def test_creating_duplicate_range_fails(self):
        custom.create_range(CustomRange)
        self.assertRaises(ValueError, custom.create_range, CustomRange)

    def test_must_have_a_text_name(self):
        try:
            custom.create_range(CustomRangeLazy)
        except ValidationError:
            pass
        else:
            self.fail("Range can't have ugettext titles")

    def test_correctly_includes_match(self):
        rng = custom.create_range(CustomRange)
        test_product = create_product(title=u"A tale")
        self.assertTrue(rng.contains_product(test_product))

    def test_correctly_excludes_nonmatch(self):
        rng = custom.create_range(CustomRange)
        test_product = create_product(title=u"B tale")
        self.assertFalse(rng.contains_product(test_product))
