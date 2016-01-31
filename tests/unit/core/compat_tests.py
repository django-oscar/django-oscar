# -*- coding: utf-8 -*-
import datetime
from django.utils import six
from django.utils.six.moves import cStringIO

from django.test import TestCase

from oscar.core.compat import UnicodeCSVWriter, existing_user_fields

class TestExistingUserFields(TestCase):

    def test_order(self):
        fields = existing_user_fields(['email', 'first_name', 'last_name'])
        self.assertEqual(fields, ['email', 'first_name', 'last_name'])


class TestUnicodeCSVWriter(TestCase):

    def test_can_write_different_values(self):
        writer = UnicodeCSVWriter(open_file=cStringIO())
        s = u'ünįcodē'
        class unicodeobj(object):
            def __str__(self):
                return s
            def __unicode__(self):
                return s
        rows = [[s, unicodeobj(), 123, datetime.date.today()], ]
        writer.writerows(rows)
        self.assertRaises(TypeError, writer.writerows, [object()])


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
