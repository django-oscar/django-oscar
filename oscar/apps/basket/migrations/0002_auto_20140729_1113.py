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
            field=models.ManyToManyField(to='voucher.Voucher', null=True, verbose_name='Vouchers', blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('line_reference', models.SlugField(max_length=128, verbose_name='Line Reference')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('price_currency', models.CharField(default=b'GBP', max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(null=True, verbose_name='Price excl. Tax', max_digits=12, decimal_places=2)),
                ('price_incl_tax', models.DecimalField(null=True, verbose_name='Price incl. Tax', max_digits=12, decimal_places=2)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('basket', models.ForeignKey(verbose_name='Basket', to='basket.Basket')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalogue.Product')),
                ('stockrecord', models.ForeignKey(to='partner.StockRecord')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Basket line',
                'verbose_name_plural': 'Basket lines',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='line',
            unique_together=set([(b'basket', b'line_reference')]),
        ),
        migrations.CreateModel(
            name='LineAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=255, verbose_name='Value')),
                ('line', models.ForeignKey(verbose_name='Line', to='basket.Line')),
                ('option', models.ForeignKey(verbose_name='Option', to='catalogue.Option')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Line attribute',
                'verbose_name_plural': 'Line attributes',
            },
            bases=(models.Model,),
        ),
    ]
