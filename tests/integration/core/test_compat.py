# -*- coding: utf-8 -*-
import codecs
import datetime
import io
import os
from tempfile import NamedTemporaryFile

from django.test import TestCase, override_settings
from django.utils.encoding import smart_str

from oscar.core.compat import UnicodeCSVWriter, existing_user_fields


class TestExistingUserFields(TestCase):
    def test_order(self):
        fields = existing_user_fields(["email", "first_name", "last_name"])
        self.assertEqual(fields, ["email", "first_name", "last_name"])


class TestUnicodeCSVWriter(TestCase):
    def test_can_write_different_values(self):
        writer = UnicodeCSVWriter(open_file=io.StringIO())
        s = "ünįcodē"
        rows = [
            [s, s, 123, datetime.date.today()],
        ]
        writer.writerows(rows)
        self.assertRaises(TypeError, writer.writerows, [object()])

    def test_context_manager(self):
        tmp_file = NamedTemporaryFile()
        with UnicodeCSVWriter(filename=tmp_file.name) as writer:
            s = "ünįcodē"
            rows = [
                [s, s, 123, datetime.date.today()],
            ]
            writer.writerows(rows)

    def test_csv_write_output(self):
        tmp_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=tmp_file.name) as writer:
            s = "ünįcodē"
            row = [s, 123, "foo-bar"]
            writer.writerows([row])

        with open(tmp_file.name, "r", encoding="utf-8") as read_file:
            content = smart_str(read_file.read(), encoding="utf-8").strip()
            self.assertEqual(content, "ünįcodē,123,foo-bar")

        # Clean up
        os.unlink(tmp_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_write_with_open_file(self):
        csv_file = NamedTemporaryFile(delete=False)
        with open(csv_file.name, "w", encoding="utf-8") as open_file:
            writer = UnicodeCSVWriter(open_file=open_file, encoding="utf-8")
            s = "ünįcodē"
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, "rb") as read_file:
            self.assertTrue(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_write_with_filename(self):
        csv_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=csv_file.name, encoding="utf-8") as writer:
            s = "ünįcodē"
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, "rb") as read_file:
            self.assertTrue(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_not_written_for_other_encodings(self):
        csv_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=csv_file.name, encoding="ascii") as writer:
            s = "boring ascii"
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, "rb") as read_file:
            self.assertFalse(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)
