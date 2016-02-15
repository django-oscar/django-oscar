# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import oscar.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0007_auto_20151207_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='full_name',
            field=models.CharField(default='', verbose_name='Full Name', max_length=255, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='full_slug',
            field=models.CharField(default='', verbose_name='Full Slug', max_length=255, editable=False, db_index=True),
            preserve_default=False,
        ),
    ]
