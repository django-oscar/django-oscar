# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from django.conf import settings
import oscar.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Code')),
                ('name', models.CharField(max_length=128, verbose_name='Name', blank=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='Users', blank=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Fulfillment partner',
                'verbose_name_plural': 'Fulfillment partners',
                'permissions': ((b'dashboard_access', b'Can access dashboard'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartnerAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(blank=True, max_length=64, verbose_name='Title', choices=[(b'Mr', 'Mr'), (b'Miss', 'Miss'), (b'Mrs', 'Mrs'), (b'Ms', 'Ms'), (b'Dr', 'Dr')])),
                ('first_name', models.CharField(max_length=255, verbose_name='First name', blank=True)),
                ('last_name', models.CharField(max_length=255, verbose_name='Last name', blank=True)),
                ('line1', models.CharField(max_length=255, verbose_name='First line of address')),
                ('line2', models.CharField(max_length=255, verbose_name='Second line of address', blank=True)),
                ('line3', models.CharField(max_length=255, verbose_name='Third line of address', blank=True)),
                ('line4', models.CharField(max_length=255, verbose_name='City', blank=True)),
                ('state', models.CharField(max_length=255, verbose_name='State/County', blank=True)),
                ('postcode', oscar.models.fields.UppercaseCharField(max_length=64, verbose_name='Post/Zip-code', blank=True)),
                ('search_text', models.TextField(verbose_name='Search text - used only for searching addresses', editable=False)),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country')),
                ('partner', models.ForeignKey(verbose_name='Partner', to='partner.Partner')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Partner address',
                'verbose_name_plural': 'Partner addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockAlert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('threshold', models.PositiveIntegerField(verbose_name='Threshold')),
                ('status', models.CharField(default=b'Open', max_length=128, verbose_name='Status', choices=[(b'Open', 'Open'), (b'Closed', 'Closed')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_closed', models.DateTimeField(null=True, verbose_name='Date Closed', blank=True)),
            ],
            options={
                'ordering': (b'-date_created',),
                'abstract': False,
                'verbose_name': 'Stock alert',
                'verbose_name_plural': 'Stock alerts',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('partner_sku', models.CharField(max_length=128, verbose_name='Partner SKU')),
                ('price_currency', models.CharField(default=b'GBP', max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(null=True, verbose_name='Price (excl. tax)', max_digits=12, decimal_places=2, blank=True)),
                ('price_retail', models.DecimalField(null=True, verbose_name='Price (retail)', max_digits=12, decimal_places=2, blank=True)),
                ('cost_price', models.DecimalField(null=True, verbose_name='Cost Price', max_digits=12, decimal_places=2, blank=True)),
                ('num_in_stock', models.PositiveIntegerField(null=True, verbose_name='Number in stock', blank=True)),
                ('num_allocated', models.IntegerField(null=True, verbose_name='Number allocated', blank=True)),
                ('low_stock_threshold', models.PositiveIntegerField(null=True, verbose_name='Low Stock Threshold', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated', db_index=True)),
                ('partner', models.ForeignKey(verbose_name='Partner', to='partner.Partner')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Stock record',
                'verbose_name_plural': 'Stock records',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='stockalert',
            name='stockrecord',
            field=models.ForeignKey(verbose_name='Stock Record', to='partner.StockRecord'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='stockrecord',
            unique_together=set([(b'partner', b'partner_sku')]),
        ),
    ]
