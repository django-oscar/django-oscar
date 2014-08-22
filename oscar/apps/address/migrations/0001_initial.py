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
                ('iso_3166_1_a2', models.CharField(verbose_name='ISO 3166-1 alpha-2', primary_key=True, serialize=False, max_length=2)),
                ('iso_3166_1_a3', models.CharField(verbose_name='ISO 3166-1 alpha-3', blank=True, max_length=3)),
                ('iso_3166_1_numeric', models.CharField(verbose_name='ISO 3166-1 numeric', blank=True, max_length=3)),
                ('printable_name', models.CharField(verbose_name='Country name', max_length=128)),
                ('name', models.CharField(verbose_name='Official name', max_length=128)),
                ('display_order', models.PositiveSmallIntegerField(verbose_name='Display order', help_text='Higher the number, higher the country in the list.', db_index=True, default=0)),
                ('is_shipping_country', models.BooleanField(verbose_name='Is shipping country', default=False, db_index=True)),
            ],
            options={
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
                'ordering': ('-display_order', 'printable_name'),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserAddress',
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
                ('phone_number', oscar.models.fields.PhoneNumberField(verbose_name='Phone number', blank=True, help_text='In case we need to call you about your order')),
                ('notes', models.TextField(verbose_name='Instructions', blank=True, help_text='Tell us anything we should know when delivering your order.')),
                ('is_default_for_shipping', models.BooleanField(verbose_name='Default shipping address?', default=False)),
                ('is_default_for_billing', models.BooleanField(verbose_name='Default billing address?', default=False)),
                ('num_orders', models.PositiveIntegerField(verbose_name='Number of Orders', default=0)),
                ('hash', models.CharField(editable=False, verbose_name='Address Hash', db_index=True, max_length=255)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('country', models.ForeignKey(verbose_name='Country', to='address.Country')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User address',
                'verbose_name_plural': 'User addresses',
                'ordering': ['-num_orders'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='useraddress',
            unique_together=set([('user', 'hash')]),
        ),
    ]
