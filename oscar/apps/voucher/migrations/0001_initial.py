# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('offer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', help_text='This will be shown in the checkout and basket once the voucher is entered', max_length=128)),
                ('code', models.CharField(verbose_name='Code', unique=True, help_text='Case insensitive / No spaces allowed', db_index=True, max_length=128)),
                ('usage', models.CharField(verbose_name='Usage', choices=[('Single use', 'Can be used once by one customer'), ('Multi-use', 'Can be used multiple times by multiple customers'), ('Once per customer', 'Can only be used once per customer')], default='Multi-use', max_length=128)),
                ('start_datetime', models.DateTimeField(verbose_name='Start datetime')),
                ('end_datetime', models.DateTimeField(verbose_name='End datetime')),
                ('num_basket_additions', models.PositiveIntegerField(verbose_name='Times added to basket', default=0)),
                ('num_orders', models.PositiveIntegerField(verbose_name='Times on orders', default=0)),
                ('total_discount', models.DecimalField(verbose_name='Total discount', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('date_created', models.DateField(auto_now_add=True)),
                ('offers', models.ManyToManyField(verbose_name='Offers', to='offer.ConditionalOffer')),
            ],
            options={
                'verbose_name': 'Voucher',
                'verbose_name_plural': 'Vouchers',
                'abstract': False,
                'get_latest_by': 'date_created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VoucherApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('date_created', models.DateField(verbose_name='Date Created', auto_now_add=True)),
                ('order', models.ForeignKey(verbose_name='Order', to='order.Order')),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('voucher', models.ForeignKey(verbose_name='Voucher', to='voucher.Voucher')),
            ],
            options={
                'verbose_name': 'Voucher Application',
                'verbose_name_plural': 'Voucher Applications',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
