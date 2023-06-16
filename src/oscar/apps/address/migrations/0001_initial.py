# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields
from django.utils.module_loading import import_string
from django.conf import settings

models_AutoField = import_string(settings.DEFAULT_AUTO_FIELD)

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('iso_3166_1_a2', models.CharField(primary_key=True, max_length=2, verbose_name='ISO 3166-1 alpha-2', serialize=False)),
                ('iso_3166_1_a3', models.CharField(max_length=3, verbose_name='ISO 3166-1 alpha-3', blank=True)),
                ('iso_3166_1_numeric', models.CharField(max_length=3, verbose_name='ISO 3166-1 numeric', blank=True)),
                ('printable_name', models.CharField(max_length=128, verbose_name='Country name')),
                ('name', models.CharField(max_length=128, verbose_name='Official name')),
                ('display_order', models.PositiveSmallIntegerField(default=0, verbose_name='Display order', db_index=True, help_text='Higher the number, higher the country in the list.')),
                ('is_shipping_country', models.BooleanField(default=False, db_index=True, verbose_name='Is shipping country')),
            ],
            options={
                'ordering': ('-display_order', 'printable_name'),
                'verbose_name_plural': 'Countries',
                'verbose_name': 'Country',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAddress',
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
                ('phone_number', oscar.models.fields.PhoneNumberField(verbose_name='Phone number', help_text='In case we need to call you about your order', blank=True)),
                ('notes', models.TextField(verbose_name='Instructions', help_text='Tell us anything we should know when delivering your order.', blank=True)),
                ('is_default_for_shipping', models.BooleanField(default=False, verbose_name='Default shipping address?')),
                ('is_default_for_billing', models.BooleanField(default=False, verbose_name='Default billing address?')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Number of Orders')),
                ('hash', models.CharField(max_length=255, editable=False, db_index=True, verbose_name='Address Hash')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(verbose_name='User', related_name='addresses', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['-num_orders'],
                'verbose_name_plural': 'User addresses',
                'verbose_name': 'User address',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='useraddress',
            unique_together=set([('user', 'hash')]),
        ),
    ]
