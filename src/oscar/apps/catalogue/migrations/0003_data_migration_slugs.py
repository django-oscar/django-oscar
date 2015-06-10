# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from oscar.core.loading import get_model

# Django database migrations require us to fetch the category model
# via apps.get_model to get an instance of the model at this point
# in time of migrations. That snapshot does not expose custom
# properties, only whatever is represented in the migration files.
# But because for our slug munging below, we need to know the slug
# separator, which is a custom property, we also load the actual
# ORM model. We MUST NOT use that to save data, we just fetch
# the property.

ORMCategory = get_model('catalogue', 'Category')


def remove_ancestor_slugs(apps, schema_editor):
    MigrationCategory = apps.get_model('catalogue', 'Category')
    for category in MigrationCategory.objects.all():
        category.slug = category.slug.split(ORMCategory._slug_separator)[-1]
        category.save()


def add_ancestor_slugs(apps, schema_editor):
    MigrationCategory = apps.get_model('catalogue', 'Category')
    for category in MigrationCategory.objects.all():
        orm_category = ORMCategory.objects.get(pk=category.pk)
        category.slug = orm_category.full_slug
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0002_auto_20150217_1221'),
    ]

    operations = [
        migrations.RunPython(remove_ancestor_slugs, add_ancestor_slugs),
    ]
