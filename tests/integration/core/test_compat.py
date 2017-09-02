# -*- coding: utf-8 -*-
import codecs
import datetime
import os
from tempfile import NamedTemporaryFile
from django.utils import six
from django.utils.encoding import smart_text
from django.utils.six.moves import cStringIO

from django.test import TestCase, override_settings

from oscar.core.compat import UnicodeCSVWriter, existing_user_fields


class unicodeobj(object):

    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s

    def __unicode__(self):
        return self.s


class TestExistingUserFields(TestCase):

    def test_order(self):
        fields = existing_user_fields(['email', 'first_name', 'last_name'])
        self.assertEqual(fields, ['email', 'first_name', 'last_name'])


class TestUnicodeCSVWriter(TestCase):

    def test_can_write_different_values(self):
        writer = UnicodeCSVWriter(open_file=cStringIO())
        s = u'ünįcodē'
        rows = [[s, unicodeobj(s), 123, datetime.date.today()], ]
        writer.writerows(rows)
        self.assertRaises(TypeError, writer.writerows, [object()])

    def test_context_manager(self):
        tmp_file = NamedTemporaryFile()
        with UnicodeCSVWriter(filename=tmp_file.name) as writer:
            s = u'ünįcodē'
            rows = [[s, unicodeobj(s), 123, datetime.date.today()], ]
            writer.writerows(rows)

    def test_csv_write_output(self):
        tmp_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=tmp_file.name) as writer:
            s = u'ünįcodē'
            row = [s, 123, 'foo-bar']
            writer.writerows([row])

        with open(tmp_file.name, 'r') as read_file:
            content = smart_text(read_file.read(), encoding='utf-8').strip()
            self.assertEqual(content, u'ünįcodē,123,foo-bar')

        # Clean up
        os.unlink(tmp_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_write_with_open_file(self):
        csv_file = NamedTemporaryFile(delete=False)
        with open(csv_file.name, 'w') as open_file:
            writer = UnicodeCSVWriter(open_file=open_file, encoding="utf-8")
            s = u'ünįcodē'
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, 'rb') as read_file:
            self.assertTrue(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_write_with_filename(self):
        csv_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=csv_file.name, encoding="utf-8") as writer:
            s = u'ünįcodē'
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, 'rb') as read_file:
            self.assertTrue(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)

    @override_settings(OSCAR_CSV_INCLUDE_BOM=True)
    def test_bom_not_written_for_other_encodings(self):
        csv_file = NamedTemporaryFile(delete=False)
        with UnicodeCSVWriter(filename=csv_file.name, encoding="ascii") as writer:
            s = 'boring ascii'
            row = [s, 123, datetime.date.today()]
            writer.writerows([row])

        with open(csv_file.name, 'rb') as read_file:
            self.assertFalse(read_file.read().startswith(codecs.BOM_UTF8))

        # Clean up
        os.unlink(csv_file.name)


class TestPython3Compatibility(TestCase):

    def test_models_define_python_3_compatible_representation(self):
        """
        In Python 2, models can define __unicode__ to get a text representation,
        in Python 3 this is achieved by defining __str__. The
        python_2_unicode_compatible decorator helps with that. We must use it
        every time we define a text representation; this test checks that it's
        used correctly.
        """
        from django.apps import apps
        models = [
            model for model in apps.get_models() if 'oscar' in repr(model)]
        invalid_models = []
        for model in models:
            # Use abstract model if it exists
            if 'oscar' in repr(model.__base__):
                model = model.__base__

            dict_ = model.__dict__
            if '__str__' in dict_:
                if six.PY2:
                    valid = '__unicode__' in dict_
                else:
                    valid = '__unicode__' not in dict_
            else:
                valid = '__unicode__' not in dict_
            if not valid:
                invalid_models.append(model)
        if invalid_models:
            self.fail(
                "Those models don't use the python_2_compatible decorator or define __unicode__: %s" % invalid_models)
