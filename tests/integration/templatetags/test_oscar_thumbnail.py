import os
from unittest.mock import patch

from django import template
from django.test import TestCase
from django.test.utils import override_settings

from oscar.test.factories.catalogue import ProductImageFactory
from oscar.test.utils import EASY_THUMBNAIL_BASEDIR, get_thumbnail_full_path


class OscarThumbnailMixin:
    # Next values will be different `sorl-thumbnail` and `easy-thumbnails`.
    crop_value = size_string_mapping = None

    def setUp(self):
        self.product_image = ProductImageFactory()
        self.context = template.Context({"image": self.product_image})
        self.template = template.Template(
            "{% load image_tags %}"
            '{% oscar_thumbnail image.original "x155" upscale=False %}'
        )
        self.template_as_context_value = template.Template(
            "{% load image_tags %}"
            '{% oscar_thumbnail image.original "x155" upscale=False as thumb %}'
            "{{ thumb.url }}"
        )

    def _test_oscar_thumbnail_tag(self, is_context_value=False):
        if is_context_value:
            thumbnail_url = self.template.render(self.context)
        else:
            thumbnail_url = self.template_as_context_value.render(self.context)
        thumbnail_full_path = get_thumbnail_full_path(thumbnail_url)
        assert os.path.isfile(
            thumbnail_full_path
        )  # `isfile` returns `True` if path is an existing regular file.

    def _test_oscar_thumbnail_tag_sizes(self):
        # Initial image size in `ProductImageFactory` - 100x200
        size_string_mapping = {
            "50x75": ["50", "75"],
            "x150": ["75", "150"],
            "50x": ["50", "100"],
        }
        for size_str, expected_sizes in size_string_mapping.items():
            tmpl = template.Template(
                "{{% load image_tags %}}"
                '{{% oscar_thumbnail image.original "{size_str}" crop="{crop_value}" as thumb %}}'
                "{{{{ thumb.width }}}}-{{{{ thumb.height }}}}".format(
                    size_str=size_str, crop_value=self.crop_value
                )
            )
            result = tmpl.render(self.context)
            sizes = result.split("-")
            assert sizes == expected_sizes

    def test_oscar_thumbnail_tag(self):
        self._test_oscar_thumbnail_tag()

    def test_oscar_thumbnail_tag_as_context_value(self):
        self._test_oscar_thumbnail_tag(is_context_value=True)

    def test_oscar_thumbnail_sizes(self):
        self._test_oscar_thumbnail_tag_sizes()

    @patch("oscar.templatetags.image_tags.ThumbnailNode._render")
    def test_doesnt_raise_if_oscar_thumbnail_debug_is_false(self, render_mock):
        render_mock.side_effect = ValueError()
        with override_settings(OSCAR_THUMBNAIL_DEBUG=True):
            with self.assertRaises(ValueError):
                self.template.render(self.context)

    @patch("oscar.templatetags.image_tags.ThumbnailNode._render")
    def test_raises_if_oscar_thumbnail_debug_is_true(self, render_mock):
        render_mock.side_effect = ValueError()
        with override_settings(OSCAR_THUMBNAIL_DEBUG=False):
            self.assertEqual(self.template.render(self.context), "")

    @patch("oscar.templatetags.image_tags.ThumbnailNode._render")
    def test_doesnt_raise_if_debug_is_false_and_oscar_thumbnail_debug_is_not_set(
        self, render_mock
    ):
        render_mock.side_effect = ValueError()
        with override_settings(DEBUG=True):
            with self.assertRaises(ValueError):
                self.template.render(self.context)

    @patch("oscar.templatetags.image_tags.ThumbnailNode._render")
    def test_raises_if_debug_is_true_and_oscar_thumbnail_debug_is_not_set(
        self, render_mock
    ):
        render_mock.side_effect = ValueError()
        with override_settings(DEBUG=False):
            self.assertEqual(self.template.render(self.context), "")


@override_settings(
    OSCAR_THUMBNAILER="oscar.core.thumbnails.SorlThumbnail",
)
class TestOscarThumbnailWithSorlThumbnail(OscarThumbnailMixin, TestCase):
    crop_value = "center"


@override_settings(
    THUMBNAIL_BASEDIR=EASY_THUMBNAIL_BASEDIR,
    OSCAR_THUMBNAILER="oscar.core.thumbnails.EasyThumbnails",
)
class TestOscarThumbnailWithEasyThumbnails(OscarThumbnailMixin, TestCase):
    crop_value = True
