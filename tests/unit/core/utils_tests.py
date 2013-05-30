from django.test import TestCase
from django.test.utils import override_settings

from oscar.core import utils


class TestSlugify(TestCase):

    def test_uses_custom_mappings(self):
        mapping = {'c++': 'cpp'}
        with override_settings(OSCAR_SLUG_MAP=mapping):
            self.assertEqual('cpp', utils.slugify('c++'))

    def test_uses_blacklist(self):
        blacklist = ['the']
        with override_settings(OSCAR_SLUG_BLACKLIST=blacklist):
            self.assertEqual('bible', utils.slugify('The Bible'))
