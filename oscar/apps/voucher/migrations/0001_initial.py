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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='This will be shown in the checkout and basket once the voucher is entered', max_length=128, verbose_name='Name')),
                ('code', models.CharField(help_text='Case insensitive / No spaces allowed', unique=True, max_length=128, verbose_name='Code', db_index=True)),
                ('usage', models.CharField(default=b'Multi-use', max_length=128, verbose_name='Usage', choices=[(b'Single use', 'Can be used once by one customer'), (b'Multi-use', 'Can be used multiple times by multiple customers'), (b'Once per customer', 'Can only be used once per customer')])),
                ('start_datetime', models.DateTimeField(verbose_name='Start datetime')),
                ('end_datetime', models.DateTimeField(verbose_name='End datetime')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Times added to basket')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Times on orders')),
                ('total_discount', models.DecimalField(default=Decimal('0.00'), verbose_name='Total discount', max_digits=12, decimal_places=2)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('offers', models.ManyToManyField(to='offer.ConditionalOffer', verbose_name='Offers')),
            ],
            options={
                'abstract': False,
                'get_latest_by': b'date_created',
                'verbose_name': 'Voucher',
                'verbose_name_plural': 'Vouchers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VoucherApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateField(auto_now_add=True, verbose_name='Date Created')),
                ('order', models.ForeignKey(verbose_name='Order', to='order.Order')),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('voucher', models.ForeignKey(verbose_name='Voucher', to='voucher.Voucher')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Voucher Application',
                'verbose_name_plural': 'Voucher Applications',
            },
            bases=(models.Model,),
        ),
    ]
