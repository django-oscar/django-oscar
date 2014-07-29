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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'User product view',
                'verbose_name_plural': 'User product views',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_product_views', models.PositiveIntegerField(default=0, verbose_name='Product Views')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Basket Additions')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Orders', db_index=True)),
                ('num_order_lines', models.PositiveIntegerField(default=0, verbose_name='Order Lines', db_index=True)),
                ('num_order_items', models.PositiveIntegerField(default=0, verbose_name='Order Items', db_index=True)),
                ('total_spent', models.DecimalField(default=Decimal('0.00'), verbose_name='Total Spent', max_digits=12, decimal_places=2)),
                ('date_last_order', models.DateTimeField(null=True, verbose_name='Last Order Date', blank=True)),
                ('user', models.OneToOneField(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'User record',
                'verbose_name_plural': 'User records',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSearch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('query', models.CharField(max_length=255, verbose_name='Search term', db_index=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'User search query',
                'verbose_name_plural': 'User search queries',
            },
            bases=(models.Model,),
        ),
    ]
