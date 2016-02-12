# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20150113_1629'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='line',
            options={'ordering': ['pk'], 'verbose_name': 'Order Line', 'verbose_name_plural': 'Order Lines'},
        ),
    ]
