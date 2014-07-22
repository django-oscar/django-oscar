# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_views', models.PositiveIntegerField(default=0, verbose_name='Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_purchases', models.PositiveIntegerField(default=0, verbose_name='Purchases', db_index=True)),
                ('score', models.FloatField(default=0.0, verbose_name='Score')),
            ],
            options={
                'ordering': [b'-num_purchases'],
                'abstract': False,
                'verbose_name': 'Product record',
                'verbose_name_plural': 'Product records',
            },
            bases=(models.Model,),
        ),
    ]
