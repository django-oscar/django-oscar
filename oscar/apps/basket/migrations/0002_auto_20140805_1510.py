# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        ('voucher', '0001_initial'),
        ('basket', '0001_initial'),
        ('partner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='vouchers',
            field=models.ManyToManyField(verbose_name='Vouchers', blank=True, to='voucher.Voucher', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('line_reference', models.SlugField(verbose_name='Line Reference', max_length=128)),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantity', default=1)),
                ('price_currency', models.CharField(verbose_name='Currency', default='GBP', max_length=12)),
                ('price_excl_tax', models.DecimalField(verbose_name='Price excl. Tax', max_digits=12, decimal_places=2, null=True)),
                ('price_incl_tax', models.DecimalField(verbose_name='Price incl. Tax', max_digits=12, decimal_places=2, null=True)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('basket', models.ForeignKey(verbose_name='Basket', to='basket.Basket')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
                ('stockrecord', models.ForeignKey(to='partner.StockRecord')),
            ],
            options={
                'verbose_name': 'Basket line',
                'verbose_name_plural': 'Basket lines',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([('basket', 'line_reference')]),
        ),
        migrations.CreateModel(
            name='LineAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('value', models.CharField(verbose_name='Value', max_length=255)),
                ('line', models.ForeignKey(verbose_name='Line', to='basket.Line')),
                ('option', models.ForeignKey(verbose_name='Option', to='catalogue.Option')),
            ],
            options={
                'verbose_name': 'Line attribute',
                'verbose_name_plural': 'Line attributes',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
