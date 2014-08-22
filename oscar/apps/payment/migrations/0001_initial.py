# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from django.conf import settings
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bankcard',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('card_type', models.CharField(verbose_name='Card Type', max_length=128)),
                ('name', models.CharField(verbose_name='Name', blank=True, max_length=255)),
                ('number', models.CharField(verbose_name='Number', max_length=32)),
                ('expiry_date', models.DateField(verbose_name='Expiry Date')),
                ('partner_reference', models.CharField(verbose_name='Partner Reference', blank=True, max_length=255)),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Bankcard',
                'verbose_name_plural': 'Bankcards',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('currency', models.CharField(verbose_name='Currency', default='GBP', max_length=12)),
                ('amount_allocated', models.DecimalField(verbose_name='Amount Allocated', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('amount_debited', models.DecimalField(verbose_name='Amount Debited', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('amount_refunded', models.DecimalField(verbose_name='Amount Refunded', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('reference', models.CharField(verbose_name='Reference', blank=True, max_length=128)),
                ('label', models.CharField(verbose_name='Label', blank=True, max_length=128)),
                ('order', models.ForeignKey(verbose_name='Order', to='order.Order')),
            ],
            options={
                'verbose_name': 'Source',
                'verbose_name_plural': 'Sources',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=128)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Code', blank=True, max_length=128, populate_from='name', help_text='This is used within forms to identify this source type', unique=True)),
            ],
            options={
                'verbose_name': 'Source Type',
                'verbose_name_plural': 'Source Types',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='source',
            name='source_type',
            field=models.ForeignKey(verbose_name='Source Type', to='payment.SourceType'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('txn_type', models.CharField(verbose_name='Type', blank=True, max_length=128)),
                ('amount', models.DecimalField(verbose_name='Amount', max_digits=12, decimal_places=2)),
                ('reference', models.CharField(verbose_name='Reference', blank=True, max_length=128)),
                ('status', models.CharField(verbose_name='Status', blank=True, max_length=128)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('source', models.ForeignKey(verbose_name='Source', to='payment.Source')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-date_created'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
