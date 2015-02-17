# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_ancestor_slugs(apps, schema_editor):
    Category = apps.get_model('catalogue', 'Category')
    for category in Category.objects.all():
        category.slug = category.slug.split(Category._slug_separator)[-1]
        category.save()


def add_ancestor_slugs(apps, schema_editor):
    Category = apps.get_model('catalogue', 'Category')
    for category in Category.objects.all():
        category.slug = category.full_slug
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0002_auto_20150217_1221'),
    ]

    operations = [
        migrations.RunPython(remove_ancestor_slugs, add_ancestor_slugs),
    ]
