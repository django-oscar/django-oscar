# coding=utf-8
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
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings

from oscar.core.loading import get_model

SluggedTestModel = get_model("model_tests_app", "sluggedtestmodel")
ChildSluggedTestModel = get_model("model_tests_app", "childsluggedtestmodel")
CustomSluggedTestModel = get_model("model_tests_app", "CustomSluggedTestModel")


class AutoSlugFieldTest(TestCase):
    def tearDown(self):
        super().tearDown()

        SluggedTestModel.objects.all().delete()

    def test_auto_create_slug(self):
        m = SluggedTestModel(title="foo")
        m.save()
        self.assertEqual(m.slug, "foo")

    def test_auto_create_next_slug(self):
        m = SluggedTestModel(title="foo")
        m.save()

        m = SluggedTestModel(title="foo")
        m.save()
        self.assertEqual(m.slug, "foo-2")

    def test_auto_create_slug_with_number(self):
        m = SluggedTestModel(title="foo 2012")
        m.save()
        self.assertEqual(m.slug, "foo-2012")

    def test_auto_update_slug_with_number(self):
        m = SluggedTestModel(title="foo 2012")
        m.save()
        m.save()
        self.assertEqual(m.slug, "foo-2012")

    def test_auto_create_unicode_slug(self):
        with override_settings(OSCAR_SLUG_ALLOW_UNICODE=True):
            m = SluggedTestModel(title="Château Margaux 1960")
            m.save()
            self.assertEqual(m.slug, "château-margaux-1960")

    def test_auto_create_next_unicode_slug(self):
        with override_settings(OSCAR_SLUG_ALLOW_UNICODE=True):
            m1 = SluggedTestModel(title="Château Margaux 1960")
            m1.save()

            m2 = SluggedTestModel(title="Château Margaux 1960")
            m2.save()

            self.assertEqual(m2.slug, "château-margaux-1960-2")

    def test_switch_to_unicode_slug(self):
        m = SluggedTestModel(title="Château Margaux 1960")
        m.save()
        self.assertEqual(m.slug, "chateau-margaux-1960")
        with override_settings(OSCAR_SLUG_ALLOW_UNICODE=True):
            m = SluggedTestModel(title="Château Margaux 1960")
            m.save()
            self.assertEqual(m.slug, "château-margaux-1960")

    def test_autoslugfield_allow_unicode_kwargs_precedence(self):
        from oscar.models.fields import AutoSlugField

        with override_settings(OSCAR_SLUG_ALLOW_UNICODE=True):
            autoslug_field = AutoSlugField(populate_from="title", allow_unicode=False)
            self.assertFalse(autoslug_field.allow_unicode)
            autoslug_field = AutoSlugField(populate_from="title")
            self.assertTrue(autoslug_field.allow_unicode)

    def test_update_slug(self):
        m = SluggedTestModel(title="foo")
        m.save()
        self.assertEqual(m.slug, "foo")

        # update m instance without using `save'
        SluggedTestModel.objects.filter(pk=m.pk).update(slug="foo-2012")
        # update m instance with new data from the db
        m = SluggedTestModel.objects.get(pk=m.pk)
        self.assertEqual(m.slug, "foo-2012")

        m.save()
        self.assertEqual(m.title, "foo")
        self.assertEqual(m.slug, "foo-2012")

        # Check slug is not overwrite
        m.title = "bar"
        m.save()
        self.assertEqual(m.title, "bar")
        self.assertEqual(m.slug, "foo-2012")

    def test_simple_slug_source(self):
        m = SluggedTestModel(title="-foo")
        m.save()
        self.assertEqual(m.slug, "foo")

        n = SluggedTestModel(title="-foo")
        n.save()
        self.assertEqual(n.slug, "foo-2")

        n.save()
        self.assertEqual(n.slug, "foo-2")

    def test_empty_slug_source(self):
        # regression test

        m = SluggedTestModel(title="")
        m.save()
        self.assertEqual(m.slug, "-2")

        n = SluggedTestModel(title="")
        n.save()
        self.assertEqual(n.slug, "-3")

        n.save()
        self.assertEqual(n.slug, "-3")

    def test_inheritance_creates_next_slug(self):
        m = SluggedTestModel(title="foo")
        m.save()

        n = ChildSluggedTestModel(title="foo")
        n.save()
        self.assertEqual(n.slug, "foo-2")

        o = SluggedTestModel(title="foo")
        o.save()
        self.assertEqual(o.slug, "foo-3")

    def test_separator_and_uppercase_options(self):
        m = CustomSluggedTestModel(title="Password reset")
        m.save()
        self.assertEqual(m.slug, "PASSWORD_RESET")

        m = CustomSluggedTestModel(title="Password reset")
        m.save()
        self.assertEqual(m.slug, "PASSWORD_RESET_2")

    def test_migration(self):
        """
        Tests making migrations with Django 1.7+'s migration framework
        """

        from django.db import migrations
        from django.db.migrations.writer import MigrationWriter

        import oscar
        from oscar.models.fields import AutoSlugField

        fields = {
            "autoslugfield": AutoSlugField(populate_from="otherfield"),
        }

        migration = type(
            str("Migration"),
            (migrations.Migration,),
            {
                "operations": [
                    migrations.CreateModel(
                        "MyModel",
                        tuple(fields.items()),
                        {"populate_from": "otherfield"},
                        (models.Model,),
                    ),
                ],
            },
        )
        writer = MigrationWriter(migration)
        output = writer.as_string()

        if isinstance(output, str):
            output = output.encode("utf-8")

        # We don't test the output formatting - that's too fragile.
        # Just make sure it runs for now, and that things look alright.
        context = {
            "migrations": migrations,
            "oscar": oscar,
        }
        result = self.safe_exec(output, context=context)
        self.assertIn("Migration", result)

    # pylint: disable=exec-used
    def safe_exec(self, string, value=None, context=None):
        loc = {}
        g = globals()
        g.update(context)
        try:
            exec(string, g, loc)
        except Exception as e:
            if value:
                self.fail(
                    "Could not exec %r (from value %r): %s" % (string.strip(), value, e)
                )
            else:
                self.fail("Could not exec %r: %s" % (string.strip(), e))
        return loc
