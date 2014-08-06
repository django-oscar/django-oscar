# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields
import oscar.models.fields.autoslugfield
from django.conf import settings


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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Code', blank=True, max_length=128, populate_from='name', unique=True)),
                ('name', models.CharField(verbose_name='Name', blank=True, max_length=128)),
                ('users', models.ManyToManyField(verbose_name='Users', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Fulfillment partner',
                'verbose_name_plural': 'Fulfillment partners',
                'permissions': (('dashboard_access', 'Can access dashboard'),),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartnerAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('title', models.CharField(verbose_name='Title', choices=[('Mr', 'Mr'), ('Miss', 'Miss'), ('Mrs', 'Mrs'), ('Ms', 'Ms'), ('Dr', 'Dr')], blank=True, max_length=64)),
                ('first_name', models.CharField(verbose_name='First name', blank=True, max_length=255)),
                ('last_name', models.CharField(verbose_name='Last name', blank=True, max_length=255)),
                ('line1', models.CharField(verbose_name='First line of address', max_length=255)),
                ('line2', models.CharField(verbose_name='Second line of address', blank=True, max_length=255)),
                ('line3', models.CharField(verbose_name='Third line of address', blank=True, max_length=255)),
                ('line4', models.CharField(verbose_name='City', blank=True, max_length=255)),
                ('state', models.CharField(verbose_name='State/County', blank=True, max_length=255)),
                ('postcode', oscar.models.fields.UppercaseCharField(verbose_name='Post/Zip-code', blank=True, max_length=64)),
                ('search_text', models.TextField(editable=False, verbose_name='Search text - used only for searching addresses')),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country')),
                ('partner', models.ForeignKey(verbose_name='Partner', to='partner.Partner')),
            ],
            options={
                'verbose_name': 'Partner address',
                'verbose_name_plural': 'Partner addresses',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('threshold', models.PositiveIntegerField(verbose_name='Threshold')),
                ('status', models.CharField(verbose_name='Status', choices=[('Open', 'Open'), ('Closed', 'Closed')], default='Open', max_length=128)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('date_closed', models.DateTimeField(verbose_name='Date Closed', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Stock alert',
                'verbose_name_plural': 'Stock alerts',
                'ordering': ('-date_created',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('partner_sku', models.CharField(verbose_name='Partner SKU', max_length=128)),
                ('price_currency', models.CharField(verbose_name='Currency', default='GBP', max_length=12)),
                ('price_excl_tax', models.DecimalField(verbose_name='Price (excl. tax)', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('price_retail', models.DecimalField(verbose_name='Price (retail)', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('cost_price', models.DecimalField(verbose_name='Cost Price', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('num_in_stock', models.PositiveIntegerField(verbose_name='Number in stock', blank=True, null=True)),
                ('num_allocated', models.IntegerField(verbose_name='Number allocated', blank=True, null=True)),
                ('low_stock_threshold', models.PositiveIntegerField(verbose_name='Low Stock Threshold', blank=True, null=True)),
                ('date_created', models.DateTimeField(verbose_name='Date created', auto_now_add=True)),
                ('date_updated', models.DateTimeField(verbose_name='Date updated', auto_now=True, db_index=True)),
                ('partner', models.ForeignKey(verbose_name='Partner', to='partner.Partner')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
            ],
            options={
                'verbose_name': 'Stock record',
                'verbose_name_plural': 'Stock records',
                'abstract': False,
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
            unique_together=set([('partner', 'partner_sku')]),
        ),
    ]
