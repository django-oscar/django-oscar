# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0004_auto_20141007_2032'),
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
            model_name='basket',
            name='vouchers',
            field=models.ManyToManyField(to='voucher.Voucher', verbose_name='Vouchers', blank=True),
        ),
        migrations.DeleteModel(
            name='LineAttribute',
        ),
    ]
