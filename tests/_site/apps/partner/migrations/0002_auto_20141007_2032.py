# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.core.utils


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockrecord',
            name='price_currency',
            field=models.CharField(default=oscar.core.utils.get_default_currency, max_length=12, verbose_name='Currency'),
        ),
    ]
