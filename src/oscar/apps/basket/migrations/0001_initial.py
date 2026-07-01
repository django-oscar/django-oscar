# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.module_loading import import_string
from django.conf import settings

models_AutoField = import_string(settings.DEFAULT_AUTO_FIELD)


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='Open', max_length=128, verbose_name='Status', choices=[('Open', 'Open - currently active'), ('Merged', 'Merged - superceded by another basket'), ('Saved', 'Saved - for items to be purchased later'), ('Frozen', 'Frozen - the basket cannot be modified'), ('Submitted', 'Submitted - has been ordered at the checkout')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_merged', models.DateTimeField(blank=True, verbose_name='Date merged', null=True)),
                ('date_submitted', models.DateTimeField(blank=True, verbose_name='Date submitted', null=True)),
            ],
            options={
                'verbose_name_plural': 'Baskets',
                'verbose_name': 'Basket',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_reference', models.SlugField(max_length=128, verbose_name='Line Reference')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('price_currency', models.CharField(default='GBP', max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Price excl. Tax', null=True)),
                ('price_incl_tax', models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Price incl. Tax', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
            ],
            options={
                'verbose_name_plural': 'Basket lines',
                'verbose_name': 'Basket line',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LineAttribute',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=255, verbose_name='Value')),
                ('line', models.ForeignKey(verbose_name='Line', related_name='attributes', to='basket.Line', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Line attributes',
                'verbose_name': 'Line attribute',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
