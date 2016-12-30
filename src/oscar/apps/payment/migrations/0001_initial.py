# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bankcard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_type', models.CharField(max_length=128, verbose_name='Card Type')),
                ('name', models.CharField(max_length=255, verbose_name='Name', blank=True)),
                ('number', models.CharField(max_length=32, verbose_name='Number')),
                ('expiry_date', models.DateField(verbose_name='Expiry Date')),
                ('partner_reference', models.CharField(max_length=255, verbose_name='Partner Reference', blank=True)),
                ('user', models.ForeignKey(verbose_name='User', related_name='bankcards', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Bankcards',
                'verbose_name': 'Bankcard',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(default='GBP', max_length=12, verbose_name='Currency')),
                ('amount_allocated', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Amount Allocated')),
                ('amount_debited', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Amount Debited')),
                ('amount_refunded', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Amount Refunded')),
                ('reference', models.CharField(max_length=128, verbose_name='Reference', blank=True)),
                ('label', models.CharField(max_length=128, verbose_name='Label', blank=True)),
                ('order', models.ForeignKey(verbose_name='Order', related_name='sources', to='order.Order', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Sources',
                'verbose_name': 'Source',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Code', editable=False, max_length=128, help_text='This is used within forms to identify this source type', blank=True)),
            ],
            options={
                'verbose_name_plural': 'Source Types',
                'verbose_name': 'Source Type',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txn_type', models.CharField(max_length=128, verbose_name='Type', blank=True)),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Amount')),
                ('reference', models.CharField(max_length=128, verbose_name='Reference', blank=True)),
                ('status', models.CharField(max_length=128, verbose_name='Status', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('source', models.ForeignKey(verbose_name='Source', related_name='transactions', to='payment.Source', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-date_created'],
                'verbose_name_plural': 'Transactions',
                'verbose_name': 'Transaction',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='source',
            name='source_type',
            field=models.ForeignKey(verbose_name='Source Type', related_name='sources', to='payment.SourceType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
