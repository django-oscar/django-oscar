# coding=utf-8

from django.test import TestCase
from django.test.utils import override_settings


class SlugFieldTest(TestCase):
    def test_slugfield_allow_unicode_kwargs_precedence(self):
        from oscar.models.fields.slugfield import SlugField

        with override_settings(OSCAR_SLUG_ALLOW_UNICODE=True):
            slug_field = SlugField(allow_unicode=False)
            self.assertFalse(slug_field.allow_unicode)
            slug_field = SlugField()
            self.assertTrue(slug_field.allow_unicode)
