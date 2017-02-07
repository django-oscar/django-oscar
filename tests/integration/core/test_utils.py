# coding=utf-8
from django.test import TestCase
from django.test.utils import override_settings

from oscar.core import utils

sluggish = lambda s: s.upper()


class TestSlugify(TestCase):

    def test_uses_custom_mappings(self):
        mapping = {'c++': 'cpp'}
        with override_settings(OSCAR_SLUG_MAP=mapping):
            self.assertEqual('cpp', utils.slugify('c++'))

    def test_uses_blacklist(self):
        blacklist = ['the']
        with override_settings(OSCAR_SLUG_BLACKLIST=blacklist):
            self.assertEqual('bible', utils.slugify('The Bible'))

    def test_handles_unicode(self):
        self.assertEqual('konig-der-strasse',
                         utils.slugify(u'König der Straße'))

    def test_works_with_custom_slugifier(self):
        for fn in [sluggish, 'tests.integration.core.test_utils.sluggish']:
            with override_settings(OSCAR_SLUG_FUNCTION=fn):
                self.assertEqual('HAM AND EGGS', utils.slugify('Ham and eggs'))
