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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('price_per_order', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Price per order')),
                ('price_per_item', models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2, verbose_name='Price per item')),
                ('free_shipping_threshold', models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Free Shipping', null=True)),
                ('countries', models.ManyToManyField(blank=True, verbose_name='Countries', to='address.Country', null=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Order and Item Charges',
                'verbose_name': 'Order and Item Charge',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upper_limit', models.DecimalField(verbose_name='Upper Limit', decimal_places=3, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], help_text='Enter upper limit of this weight band in kg. The lower limit will be determined by the other weight bands.', max_digits=12)),
                ('charge', models.DecimalField(max_digits=12, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Charge')),
            ],
            options={
                'ordering': ['method', 'upper_limit'],
                'verbose_name_plural': 'Weight Bands',
                'verbose_name': 'Weight Band',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WeightBased',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Slug', max_length=128, editable=False, blank=True)),
                ('name', models.CharField(unique=True, max_length=128, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('default_weight', models.DecimalField(validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Default Weight', default=Decimal('0.000'), max_digits=12, decimal_places=3, help_text='Default product weight in kg when no weight attribute is defined')),
                ('countries', models.ManyToManyField(blank=True, verbose_name='Countries', to='address.Country', null=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Weight-based Shipping Methods',
                'verbose_name': 'Weight-based Shipping Method',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='weightband',
            name='method',
            field=models.ForeignKey(verbose_name='Method', related_name='bands', to='shipping.WeightBased', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
