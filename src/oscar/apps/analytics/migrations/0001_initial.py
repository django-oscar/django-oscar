# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_views', models.PositiveIntegerField(default=0, verbose_name='Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_purchases', models.PositiveIntegerField(default=0, db_index=True, verbose_name='Purchases')),
                ('score', models.FloatField(default=0.0, verbose_name='Score')),
            ],
            options={
                'ordering': ['-num_purchases'],
                'verbose_name_plural': 'Product records',
                'verbose_name': 'Product record',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProductView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
            ],
            options={
                'verbose_name_plural': 'User product views',
                'verbose_name': 'User product view',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_product_views', models.PositiveIntegerField(default=0, verbose_name='Product Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_orders', models.PositiveIntegerField(default=0, db_index=True, verbose_name='Orders')),
                ('num_order_lines', models.PositiveIntegerField(default=0, db_index=True, verbose_name='Order Lines')),
                ('num_order_items', models.PositiveIntegerField(default=0, db_index=True, verbose_name='Order Items')),
                ('total_spent', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Total Spent')),
                ('date_last_order', models.DateTimeField(blank=True, verbose_name='Last Order Date', null=True)),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL,
                                              on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'User records',
                'verbose_name': 'User record',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSearch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(max_length=255, db_index=True, verbose_name='Search term')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User search queries',
                'verbose_name': 'User search query',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
