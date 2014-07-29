# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderAndItemCharges',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Slug')),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('price_per_order', models.DecimalField(default=Decimal('0.00'), verbose_name='Price per order', max_digits=12, decimal_places=2)),
                ('price_per_item', models.DecimalField(default=Decimal('0.00'), verbose_name='Price per item', max_digits=12, decimal_places=2)),
                ('free_shipping_threshold', models.DecimalField(null=True, verbose_name='Free Shipping', max_digits=12, decimal_places=2, blank=True)),
                ('countries', models.ManyToManyField(to='address.Country', null=True, verbose_name='Countries', blank=True)),
            ],
            options={
                'ordering': [b'name'],
                'abstract': False,
                'verbose_name': 'Order and Item Charge',
                'verbose_name_plural': 'Order and Item Charges',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('upper_limit', models.DecimalField(help_text='Enter upper limit of this weight band in kg. The lower limit will be determined by the other weight bands.', verbose_name='Upper Limit', max_digits=12, decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('charge', models.DecimalField(verbose_name='Charge', max_digits=12, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
            ],
            options={
                'ordering': [b'method', b'upper_limit'],
                'abstract': False,
                'verbose_name': 'Weight Band',
                'verbose_name_plural': 'Weight Bands',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBased',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, blank=True, unique=True, verbose_name='Slug')),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('default_weight', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], help_text='Default product weight in kg when no weight attribute is defined', verbose_name='Default Weight')),
                ('countries', models.ManyToManyField(to='address.Country', null=True, verbose_name='Countries', blank=True)),
            ],
            options={
                'ordering': [b'name'],
                'abstract': False,
                'verbose_name': 'Weight-based Shipping Method',
                'verbose_name_plural': 'Weight-based Shipping Methods',
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
