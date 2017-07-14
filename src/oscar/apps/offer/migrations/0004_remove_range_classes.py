# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0003_auto_20150513_1731'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='range',
            name='classes',
        ),
    ]
