# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communicationeventtype',
            name='category',
            field=models.CharField(choices=[('Order related', 'Order related'), ('User related', 'User related')], verbose_name='Category', max_length=255, default='Order related'),
        ),
    ]
