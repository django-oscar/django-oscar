# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('iso_3166_1_a2', models.CharField(max_length=2, serialize=False, verbose_name='ISO 3166-1 alpha-2', primary_key=True)),
                ('iso_3166_1_a3', models.CharField(max_length=3, verbose_name='ISO 3166-1 alpha-3', blank=True)),
                ('iso_3166_1_numeric', models.CharField(max_length=3, verbose_name='ISO 3166-1 numeric', blank=True)),
                ('printable_name', models.CharField(max_length=128, verbose_name='Country name')),
                ('name', models.CharField(max_length=128, verbose_name='Official name')),
                ('display_order', models.PositiveSmallIntegerField(default=0, help_text='Higher the number, higher the country in the list.', verbose_name='Display order', db_index=True)),
                ('is_shipping_country', models.BooleanField(default=False, db_index=True, verbose_name='Is shipping country')),
            ],
            options={
                'ordering': (b'-display_order', b'printable_name'),
                'abstract': False,
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAddress',
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
                ('phone_number', oscar.models.fields.PhoneNumberField(help_text='In case we need to call you about your order', verbose_name='Phone number', blank=True)),
                ('notes', models.TextField(help_text='Tell us anything we should know when delivering your order.', verbose_name='Instructions', blank=True)),
                ('is_default_for_shipping', models.BooleanField(default=False, verbose_name='Default shipping address?')),
                ('is_default_for_billing', models.BooleanField(default=False, verbose_name='Default billing address?')),
                ('num_orders', models.PositiveIntegerField(default=0, verbose_name='Number of Orders')),
                ('hash', models.CharField(verbose_name='Address Hash', max_length=255, editable=False, db_index=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': [b'-num_orders'],
                'abstract': False,
                'verbose_name': 'User address',
                'verbose_name_plural': 'User addresses',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='useraddress',
            unique_together=set([(b'user', b'hash')]),
        ),
    ]
