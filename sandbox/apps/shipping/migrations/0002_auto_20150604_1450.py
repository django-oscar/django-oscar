# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderanditemcharges',
            name='countries',
            field=models.ManyToManyField(to='address.Country', verbose_name='Countries', blank=True),
        ),
        migrations.AlterField(
            model_name='weightbased',
            name='countries',
            field=models.ManyToManyField(to='address.Country', verbose_name='Countries', blank=True),
        ),
    ]
