# coding=utf-8
from django.test import TestCase
from django.test.utils import override_settings

from oscar.core import utils


# pylint: disable=unused-argument
def sluggish(value, allow_unicode=False):
    return value.upper()


class TestSlugify(TestCase):
    def test_default_unicode_to_ascii(self):
        self.assertEqual("konig-der-straxdfe", utils.slugify("König der Straße"))
        self.assertEqual("not-fancy", utils.slugify("Not fancy"))
        self.assertEqual("u4e01u4e02-u4e03u4e04u4e05", utils.slugify("丁丂 七丄丅"))

    @override_settings(OSCAR_SLUG_ALLOW_UNICODE=True)
    def test_allow_unicode(self):
        self.assertEqual("könig-der-straße", utils.slugify("König der Straße"))
        self.assertEqual("丁丂-七丄丅", utils.slugify("丁丂 七丄丅"))
        self.assertEqual("not-fancy", utils.slugify("Not fancy"))

    @override_settings(OSCAR_SLUG_FUNCTION="tests.integration.core.test_utils.sluggish")
    def test_custom_slugifier(self):
        self.assertEqual("HAM AND EGGS", utils.slugify("Ham and eggs"))

    @override_settings(OSCAR_SLUG_MAP={"c++": "cpp"})
    def test_uses_custom_mappings(self):
        self.assertEqual("cpp", utils.slugify("c++"))

    @override_settings(OSCAR_SLUG_BLACKLIST=["the"])
    def test_uses_blacklist(self):
        self.assertEqual("bible", utils.slugify("The Bible"))

    @override_settings(OSCAR_SLUG_BLACKLIST=["the", "bible"])
    def test_uses_blacklist_doesnt_reduce_to_nothing(self):
        self.assertEqual("bible", utils.slugify("The Bible"))
