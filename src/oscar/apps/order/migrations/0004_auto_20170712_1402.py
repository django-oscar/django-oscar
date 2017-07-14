# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20150113_1629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lineattribute',
            name='line',
        ),
        migrations.RemoveField(
            model_name='lineattribute',
            name='option',
        ),
        migrations.AlterField(
            model_name='order',
            name='guest_email',
            field=models.EmailField(max_length=254, verbose_name='Guest email address', blank=True),
        ),
        migrations.DeleteModel(
            name='LineAttribute',
        ),
    ]
