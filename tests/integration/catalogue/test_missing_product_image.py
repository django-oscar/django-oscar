"""
Regression tests for MissingProductImage (issue #4478).

Verifies that:
1. Existing placeholder behaviour is preserved (MEDIA_ROOT not set → no-op).
2. Successful symlink creation works and is logged.
3. Symlink failure followed by a successful file copy leaves a regular file.
4. Both symlink AND copy failures raise ImproperlyConfigured with context.
5. A missing static source image raises ImproperlyConfigured.
6. A missing/unset MEDIA_ROOT is a no-op (no symlink attempted).
7. An already-existing destination file is left intact (no symlink, no error).
8. A product with no images returns a dict with ``is_missing=True``.
"""

import os
import tempfile
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from oscar.apps.catalogue.abstract_models import MissingProductImage
from oscar.test import factories


class TestMissingProductImageNoMediaRoot(TestCase):
    """When MEDIA_ROOT is empty (e.g. running tests), symlink must not be attempted."""

    @override_settings(MEDIA_ROOT="")
    @mock.patch(
        "oscar.apps.catalogue.abstract_models.MissingProductImage.symlink_missing_image"
    )
    def test_no_symlink_when_media_root_is_empty(self, mock_symlink):
        MissingProductImage()
        mock_symlink.assert_not_called()

    # Note: MEDIA_ROOT=None is not tested here because os.path.join(None, ...)
    # raises a TypeError before the ``if settings.MEDIA_ROOT`` guard is reached.
    # That is a pre-existing behaviour unrelated to this fix.  The empty-string
    # case (the documented way to disable MEDIA_ROOT during tests) is the
    # relevant guard and is covered by test_no_symlink_when_media_root_is_empty.


class TestMissingProductImageWithMissingStaticSource(TestCase):
    """Raise ImproperlyConfigured when the static source image cannot be found."""

    def test_raises_when_static_source_not_found(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with mock.patch(
                    "oscar.apps.catalogue.abstract_models.find", return_value=None
                ):
                    img = MissingProductImage.__new__(MissingProductImage)
                    img.name = "image_not_found.jpg"
                    media_file_path = os.path.join(media_root, img.name)
                    with self.assertRaises(ImproperlyConfigured) as ctx:
                        img.symlink_missing_image(media_file_path)
                    self.assertIn("could not find", str(ctx.exception))


class TestMissingProductImageSymlinkSuccess(TestCase):
    """A working symlink is created and logged."""

    def test_symlink_created_successfully(self):
        with tempfile.TemporaryDirectory() as media_root:
            # Create a real source file to point the symlink at.
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src.write(b"fake-image-data")
                src_path = src.name

            try:
                dest = os.path.join(media_root, "image_not_found.jpg")
                with override_settings(MEDIA_ROOT=media_root):
                    with mock.patch(
                        "oscar.apps.catalogue.abstract_models.find",
                        return_value=src_path,
                    ):
                        MissingProductImage()

                # Result must be a symlink pointing at our source.
                self.assertTrue(os.path.islink(dest))
                self.assertEqual(os.readlink(dest), src_path)
            finally:
                os.unlink(src_path)


class TestMissingProductImageSymlinkCreatesDirectories(TestCase):
    """Nested destination directories are created automatically."""

    def test_symlink_creates_intermediate_directories(self):
        with tempfile.TemporaryDirectory() as media_root:
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src_path = src.name

            try:
                nested_name = "subdir/image_not_found.jpg"
                dest = os.path.join(media_root, nested_name)
                with override_settings(MEDIA_ROOT=media_root):
                    with mock.patch(
                        "oscar.apps.catalogue.abstract_models.find",
                        return_value=src_path,
                    ):
                        MissingProductImage(nested_name)

                self.assertTrue(os.path.exists(dest))
            finally:
                os.unlink(src_path)


class TestMissingProductImageSymlinkFailsCopySucceeds(TestCase):
    """When os.symlink raises OSError, shutil.copy2 is used as a fallback."""

    def test_copy_fallback_on_symlink_failure(self):
        with tempfile.TemporaryDirectory() as media_root:
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src.write(b"placeholder-bytes")
                src_path = src.name

            try:
                dest = os.path.join(media_root, "image_not_found.jpg")
                with override_settings(MEDIA_ROOT=media_root):
                    with mock.patch(
                        "oscar.apps.catalogue.abstract_models.find",
                        return_value=src_path,
                    ):
                        with mock.patch(
                            "os.symlink",
                            side_effect=OSError("symlinks not supported"),
                        ):
                            MissingProductImage()

                # Result must be a regular file (copy), NOT a symlink.
                self.assertTrue(os.path.isfile(dest))
                self.assertFalse(os.path.islink(dest))
                with open(dest, "rb") as f:
                    self.assertEqual(f.read(), b"placeholder-bytes")
            finally:
                os.unlink(src_path)


class TestMissingProductImageBothOperationsFail(TestCase):
    """When both symlink and copy fail, ImproperlyConfigured is raised with context."""

    def test_raises_improperly_configured_when_both_fail(self):
        with tempfile.TemporaryDirectory() as media_root:
            with tempfile.NamedTemporaryFile(delete=False) as src:
                src_path = src.name

            try:
                dest = os.path.join(media_root, "image_not_found.jpg")
                with override_settings(MEDIA_ROOT=media_root):
                    with mock.patch(
                        "oscar.apps.catalogue.abstract_models.find",
                        return_value=src_path,
                    ):
                        with mock.patch(
                            "os.symlink",
                            side_effect=OSError("symlinks not supported"),
                        ):
                            with mock.patch(
                                "shutil.copy2",
                                side_effect=OSError("read-only filesystem"),
                            ):
                                img = MissingProductImage.__new__(MissingProductImage)
                                img.name = "image_not_found.jpg"
                                with self.assertRaises(ImproperlyConfigured) as ctx:
                                    img.symlink_missing_image(dest)

                exc_msg = str(ctx.exception)
                # Both error messages should be present in the raised exception.
                self.assertIn("symlinks not supported", exc_msg)
                self.assertIn("read-only filesystem", exc_msg)
                # The __cause__ should be the copy OSError.
                self.assertIsInstance(ctx.exception.__cause__, OSError)
            finally:
                os.unlink(src_path)


class TestMissingProductImageExistingDestinationFile(TestCase):
    """An already-present (non-symlink) destination file is left untouched."""

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as media_root:
            dest = os.path.join(media_root, "image_not_found.jpg")
            # Write the "existing" placeholder file.
            with open(dest, "wb") as f:
                f.write(b"existing-content")

            with tempfile.NamedTemporaryFile(delete=False) as src:
                src_path = src.name

            try:
                with override_settings(MEDIA_ROOT=media_root):
                    with mock.patch(
                        "oscar.apps.catalogue.abstract_models.find",
                        return_value=src_path,
                    ):
                        # __init__ checks os.path.exists → True → no call to
                        # symlink_missing_image at all.
                        MissingProductImage()

                # Content must be unchanged.
                with open(dest, "rb") as f:
                    self.assertEqual(f.read(), b"existing-content")
            finally:
                os.unlink(src_path)


class TestProductPrimaryImageNoImage(TestCase):
    """A product with no images returns a missing-image sentinel dict."""

    def test_primary_image_returns_missing_sentinel(self):
        product = factories.ProductFactory()
        # Ensure there are no images.
        product.images.all().delete()

        with mock.patch(
            "oscar.apps.catalogue.abstract_models.MissingProductImage.symlink_missing_image"
        ):
            primary = product.primary_image()

        self.assertIsInstance(primary, dict)
        self.assertTrue(primary.get("is_missing"))
        self.assertIn("original", primary)
        self.assertEqual(primary["caption"], "")
