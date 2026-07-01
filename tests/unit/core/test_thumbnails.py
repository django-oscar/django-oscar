from django.test import TestCase, override_settings

from oscar.core.thumbnails import get_thumbnailer
from oscar.test.utils import EASY_THUMBNAIL_BASEDIR, ThumbnailMixin


class TestThumbnailer(ThumbnailMixin, TestCase):
    def _test_thumbnails_deletion(self, thumbnails_full_paths):
        thumbnailer = get_thumbnailer()

        for image in self.images:
            thumbnailer.delete_thumbnails(image.original)

        self._test_thumbnails_not_exist(thumbnails_full_paths)

    def _test_thumbnailer(self, images_qty=5):
        self.create_product_images(qty=images_qty)
        thumbnails_full_paths = self.create_thumbnails()
        self._test_thumbnails_deletion(thumbnails_full_paths)

    @override_settings(
        OSCAR_THUMBNAILER="oscar.core.thumbnails.SorlThumbnail",
    )
    def test_sorl_thumbnail(self):
        self._test_thumbnailer()

    @override_settings(
        THUMBNAIL_BASEDIR=EASY_THUMBNAIL_BASEDIR,
        OSCAR_THUMBNAILER="oscar.core.thumbnails.EasyThumbnails",
    )
    def test_easy_thumbnails(self):
        self._test_thumbnailer()
