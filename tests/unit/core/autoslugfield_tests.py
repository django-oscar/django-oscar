"""
AutoSlugField taken from django-extensions at
15d3eb305957cee4768dd86e44df1bdad341a10e
Uses Oscar's slugify function instead of Django's

Copyright (c) 2007 Michael Trier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import unittest
import django
from django.db import models
from django.test import TestCase

from oscar.core.loading import get_model

SluggedTestModel = get_model('model_tests_app', 'sluggedtestmodel')
ChildSluggedTestModel = get_model('model_tests_app', 'childsluggedtestmodel')
CustomSluggedTestModel = get_model('model_tests_app', 'CustomSluggedTestModel')



class AutoSlugFieldTest(TestCase):
    def tearDown(self):
        super(AutoSlugFieldTest, self).tearDown()

        SluggedTestModel.objects.all().delete()

    def testAutoCreateSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

    def testAutoCreateNextSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def testAutoCreateSlugWithNumber(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def testAutoUpdateSlugWithNumber(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def testUpdateSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        # update m instance without using `save'
        SluggedTestModel.objects.filter(pk=m.pk).update(slug='foo-2012')
        # update m instance with new data from the db
        m = SluggedTestModel.objects.get(pk=m.pk)
        self.assertEqual(m.slug, 'foo-2012')

        m.save()
        self.assertEqual(m.title, 'foo')
        self.assertEqual(m.slug, 'foo-2012')

        # Check slug is not overwrite
        m.title = 'bar'
        m.save()
        self.assertEqual(m.title, 'bar')
        self.assertEqual(m.slug, 'foo-2012')

    def testSimpleSlugSource(self):
        m = SluggedTestModel(title='-foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        n = SluggedTestModel(title='-foo')
        n.save()
        self.assertEqual(n.slug, 'foo-2')

        n.save()
        self.assertEqual(n.slug, 'foo-2')

    def testEmptySlugSource(self):
        # regression test

        m = SluggedTestModel(title='')
        m.save()
        self.assertEqual(m.slug, '-2')

        n = SluggedTestModel(title='')
        n.save()
        self.assertEqual(n.slug, '-3')

        n.save()
        self.assertEqual(n.slug, '-3')

    def testInheritanceCreatesNextSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        n = ChildSluggedTestModel(title='foo')
        n.save()
        self.assertEqual(n.slug, 'foo-2')

        o = SluggedTestModel(title='foo')
        o.save()
        self.assertEqual(o.slug, 'foo-3')

    def test_separator_and_uppercase_options(self):
        m = CustomSluggedTestModel(title="Password reset")
        m.save()
        self.assertEqual(m.slug, 'PASSWORD_RESET')

        m = CustomSluggedTestModel(title="Password reset")
        m.save()
        self.assertEqual(m.slug, 'PASSWORD_RESET_2')

    @unittest.skipIf(django.VERSION < (1, 7),
                     "Migrations are handled by south in Django <1.7")
    def test_17_migration(self):
        """
        Tests making migrations with Django 1.7+'s migration framework
        """

        import oscar
        from django.db import migrations
        from django.db.migrations.writer import MigrationWriter
        from django.utils import six
        from oscar.models.fields import AutoSlugField
        fields = {
            'autoslugfield': AutoSlugField(populate_from='otherfield'),
        }

        migration = type(str("Migration"), (migrations.Migration,), {
            "operations": [
                migrations.CreateModel("MyModel", tuple(fields.items()),
                                       {'populate_from': 'otherfield'},
                                       (models.Model,)),
            ],
        })
        writer = MigrationWriter(migration)
        output = writer.as_string()
        # It should NOT be unicode.
        self.assertIsInstance(output, six.binary_type,
                              "Migration as_string returned unicode")
        # We don't test the output formatting - that's too fragile.
        # Just make sure it runs for now, and that things look alright.
        context = {
            'migrations': migrations,
            'oscar': oscar,
        }
        result = self.safe_exec(output, context=context)
        self.assertIn("Migration", result)

    def safe_exec(self, string, value=None, context=None):
        l = {}
        g = globals()
        g.update(context)
        try:
            exec(string, g, l)
        except Exception as e:
            if value:
                self.fail("Could not exec %r (from value %r): %s" % (
                    string.strip(), value, e))
            else:
                self.fail("Could not exec %r: %s" % (string.strip(), e))
        return l
