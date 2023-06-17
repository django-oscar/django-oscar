# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
import oscar.models.fields
from django.utils.module_loading import import_string
from django.conf import settings

models_AutoField = import_string(settings.DEFAULT_AUTO_FIELD)



class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        ('address', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Code', max_length=128, editable=False, blank=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name', blank=True)),
                ('users', models.ManyToManyField(related_name='partners', blank=True, verbose_name='Users', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name_plural': 'Fulfillment partners',
                'verbose_name': 'Fulfillment partner',
                'abstract': False,
                'permissions': (('dashboard_access', 'Can access dashboard'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartnerAddress',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(verbose_name='Title', max_length=64, blank=True, choices=[('Mr', 'Mr'), ('Miss', 'Miss'), ('Mrs', 'Mrs'), ('Ms', 'Ms'), ('Dr', 'Dr')])),
                ('first_name', models.CharField(max_length=255, verbose_name='First name', blank=True)),
                ('last_name', models.CharField(max_length=255, verbose_name='Last name', blank=True)),
                ('line1', models.CharField(max_length=255, verbose_name='First line of address')),
                ('line2', models.CharField(max_length=255, verbose_name='Second line of address', blank=True)),
                ('line3', models.CharField(max_length=255, verbose_name='Third line of address', blank=True)),
                ('line4', models.CharField(max_length=255, verbose_name='City', blank=True)),
                ('state', models.CharField(max_length=255, verbose_name='State/County', blank=True)),
                ('postcode', oscar.models.fields.UppercaseCharField(max_length=64, verbose_name='Post/Zip-code', blank=True)),
                ('search_text', models.TextField(editable=False, verbose_name='Search text - used only for searching addresses')),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country', on_delete=models.CASCADE)),
                ('partner', models.ForeignKey(verbose_name='Partner', related_name='addresses', to='partner.Partner', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Partner addresses',
                'verbose_name': 'Partner address',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockAlert',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.PositiveIntegerField(verbose_name='Threshold')),
                ('status', models.CharField(default='Open', max_length=128, verbose_name='Status', choices=[('Open', 'Open'), ('Closed', 'Closed')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_closed', models.DateTimeField(blank=True, verbose_name='Date Closed', null=True)),
            ],
            options={
                'ordering': ('-date_created',),
                'verbose_name_plural': 'Stock alerts',
                'verbose_name': 'Stock alert',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StockRecord',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partner_sku', models.CharField(max_length=128, verbose_name='Partner SKU')),
                ('price_currency', models.CharField(default='GBP', max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Price (excl. tax)', null=True)),
                ('price_retail', models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Price (retail)', null=True)),
                ('cost_price', models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Cost Price', null=True)),
                ('num_in_stock', models.PositiveIntegerField(blank=True, verbose_name='Number in stock', null=True)),
                ('num_allocated', models.IntegerField(blank=True, verbose_name='Number allocated', null=True)),
                ('low_stock_threshold', models.PositiveIntegerField(blank=True, verbose_name='Low Stock Threshold', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date updated')),
                ('partner', models.ForeignKey(verbose_name='Partner', related_name='stockrecords', to='partner.Partner', on_delete=models.CASCADE)),
                ('product', models.ForeignKey(verbose_name='Product', related_name='stockrecords', to='catalogue.Product', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Stock records',
                'verbose_name': 'Stock record',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='stockrecord',
            unique_together=set([('partner', 'partner_sku')]),
        ),
        migrations.AddField(
            model_name='stockalert',
            name='stockrecord',
            field=models.ForeignKey(verbose_name='Stock Record', related_name='alerts', to='partner.StockRecord', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
