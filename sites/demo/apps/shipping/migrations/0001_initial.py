# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators
import oscar.models.fields.autoslugfield


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderAndItemCharges',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Slug', blank=True, max_length=128, populate_from='name', unique=True)),
                ('name', models.CharField(verbose_name='Name', unique=True, max_length=128)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('price_per_order', models.DecimalField(verbose_name='Price per order', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('price_per_item', models.DecimalField(verbose_name='Price per item', max_digits=12, decimal_places=2, default=Decimal('0.00'))),
                ('free_shipping_threshold', models.DecimalField(verbose_name='Free Shipping', max_digits=12, decimal_places=2, blank=True, null=True)),
                ('countries', models.ManyToManyField(verbose_name='Countries', blank=True, to='address.Country', null=True)),
            ],
            options={
                'verbose_name': 'Order and Item Charge',
                'verbose_name_plural': 'Order and Item Charges',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBand',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('upper_limit', models.DecimalField(verbose_name='Upper Limit', max_digits=12, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], help_text='Enter upper limit of this weight band in kg. The lower limit will be determined by the other weight bands.')),
                ('charge', models.DecimalField(verbose_name='Charge', max_digits=12, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
            ],
            options={
                'verbose_name': 'Weight Band',
                'verbose_name_plural': 'Weight Bands',
                'ordering': ['method', 'upper_limit'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBased',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Slug', blank=True, max_length=128, populate_from='name', unique=True)),
                ('name', models.CharField(verbose_name='Name', unique=True, max_length=128)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('default_weight', models.DecimalField(verbose_name='Default Weight', decimal_places=3, default=Decimal('0.000'), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], help_text='Default product weight in kg when no weight attribute is defined')),
                ('countries', models.ManyToManyField(verbose_name='Countries', blank=True, to='address.Country', null=True)),
            ],
            options={
                'verbose_name': 'Weight-based Shipping Method',
                'verbose_name_plural': 'Weight-based Shipping Methods',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='weightband',
            name='method',
            field=models.ForeignKey(verbose_name='Method', to='shipping.WeightBased'),
            preserve_default=True,
        ),
    ]
