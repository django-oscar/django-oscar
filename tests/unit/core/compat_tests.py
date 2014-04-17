# -*- coding: utf-8 -*-
import datetime
from six.moves import cStringIO

from django.test import TestCase

from oscar.core.compat import UnicodeCSVWriter


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
