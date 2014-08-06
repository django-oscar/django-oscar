# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productrecord',
            name='product',
            field=models.OneToOneField(verbose_name='Product', to='catalogue.Product'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='UserProductView',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User product view',
                'verbose_name_plural': 'User product views',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('num_product_views', models.PositiveIntegerField(verbose_name='Product Views', default=0)),
                ('num_basket_additions', models.PositiveIntegerField(verbose_name='Basket Additions', default=0)),
                ('num_orders', models.PositiveIntegerField(verbose_name='Orders', db_index=True, default=0)),
                ('num_order_lines', models.PositiveIntegerField(verbose_name='Order Lines', db_index=True, default=0)),
                ('num_order_items', models.PositiveIntegerField(verbose_name='Order Items', db_index=True, default=0)),
                ('total_spent', models.DecimalField(verbose_name='Total Spent', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('date_last_order', models.DateTimeField(verbose_name='Last Order Date', blank=True, null=True)),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User record',
                'verbose_name_plural': 'User records',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSearch',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('query', models.CharField(verbose_name='Search term', db_index=True, max_length=255)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User search query',
                'verbose_name_plural': 'User search queries',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
