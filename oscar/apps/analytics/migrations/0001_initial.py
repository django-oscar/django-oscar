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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('num_views', models.PositiveIntegerField(verbose_name='Views', default=0)),
                ('num_basket_additions', models.PositiveIntegerField(verbose_name='Basket Additions', default=0)),
                ('num_purchases', models.PositiveIntegerField(verbose_name='Purchases', db_index=True, default=0)),
                ('score', models.FloatField(verbose_name='Score', default=0.0)),
            ],
            options={
                'verbose_name': 'Product record',
                'verbose_name_plural': 'Product records',
                'ordering': ['-num_purchases'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
