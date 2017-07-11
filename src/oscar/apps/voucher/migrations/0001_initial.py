# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
        ('offer', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Name', max_length=128, help_text='This will be shown in the checkout and basket once the voucher is entered')),
                ('code', models.CharField(max_length=128, verbose_name='Code', unique=True, db_index=True, help_text='Case insensitive / No spaces allowed')),
                ('usage', models.CharField(default='Multi-use', max_length=128, verbose_name='Usage', choices=[('Single use', 'Can be used once by one customer'), ('Multi-use', 'Can be used multiple times by multiple customers'), ('Once per customer', 'Can only be used once per customer')])),
                ('start_datetime', models.DateTimeField(verbose_name='Start datetime')),
                ('end_datetime', models.DateTimeField(verbose_name='End datetime')),
                ('num_basket_additions', models.PositiveIntegerField(default=0, verbose_name='Times added to basket')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Times on orders')),
                ('total_discount', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Total discount')),
                ('date_created', models.DateField(auto_now_add=True)),
                ('offers', models.ManyToManyField(related_name='vouchers', verbose_name='Offers', to='offer.ConditionalOffer')),
            ],
            options={
                'verbose_name_plural': 'Vouchers',
                'get_latest_by': 'date_created',
                'verbose_name': 'Voucher',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VoucherApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateField(auto_now_add=True, verbose_name='Date Created')),
                ('order', models.ForeignKey(verbose_name='Order', to='order.Order', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, verbose_name='User', to=settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)),
                ('voucher', models.ForeignKey(verbose_name='Voucher', related_name='applications', to='voucher.Voucher', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Voucher Applications',
                'verbose_name': 'Voucher Application',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
