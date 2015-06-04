# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20141007_2032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='date_placed',
            field=models.DateTimeField(db_index=True),
            preserve_default=True,
        ),
    ]
