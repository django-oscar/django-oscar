# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockrecord',
            name='offer_name',
            field=models.CharField(null=True, max_length=128, blank=True),
            preserve_default=True,
        ),
    ]
